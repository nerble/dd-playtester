# Operating Instructions

## November 19 Selector Boundary

Ordinary dispatch and frontier diagnosis now share the runtime safety
predicate. Missing source HP, damage, critical, or swiftness modifiers remain
visible as evidence, but they are not hard blockers by themselves. The compact
ordinary handoff and stale-consider ranking use the same predicate as the live
selector, while genuine source hazards, live negative `consider`, crowd, loss,
route, and provisioning evidence remain strict. A read-only replay of Dorrik's
level-46 checkpoint confirmed 62 current-band candidates and 58 runtime-safe
candidates; its zero executable handoffs came from recorded game evidence, not
source-output estimates. Focused campaign tests pass; this was not another
daily regression batch.
The next bounded resumes reached checkpoints **85119**, **85125**, **85134**,
**85149**, and **85155**, then **85160** through **85184**. Dorrik admitted the
exact Ra source special to a real live visit and recorded a **1,480** XP loss;
the repaired absence handoff rotated once to Hera and recorded a **1,063** XP
loss. Checkpoint **85149** acquired Sanctuary from the Alchemist for **390 XP**;
**85160** gained **750 XP** from source gear, while **85178** restored
provisions and **85173/85184** recorded safe, non-productive hunt boundaries.
The earlier checkpoint **85077** remains the successful kill proof, and the
Golden Buddha partial-XP record remains valid. This is an open evidence
boundary, not a reboot requirement.

Special procedures are not a target veto. Any exact source-matched procedure,
including aggressive, poison, breath, caster, and psionic specials whose
static output estimates are incomplete, reaches live identity and `consider`
without a static Sanctuary, cure, damage, output, or energy-containment
requirement. The starter records and reacts to the observed effect alongside
the normal route, crowd, provisioning, recovery, and own-health gates. Keep
specific source-proven route hazards, identity mismatches, scripts, crowds,
and player relocation strict; the special name itself is never a closure.

Required-gear carrier ranking follows the same boundary. Unknown HP, damage,
critical, or swiftness modifiers may leave a carrier marked `reject` for
reporting, but output-only labels do not close an otherwise source-eligible
required-loot route. Route hazards, specials, crowds, identity, level, losses,
and carrying checks remain hard gates. A source peak/critical damage budget is
also report evidence, not a carrier admission gate; the live stop owns Dorrik's
own health floor and exact hazard checks.
A failed source-gear segment with no run and zero commands is repaired as a
pre-dispatch setup failure, not counted as a route attempt, so its exact carrier
can be selected again on the next bounded resume.
The same distinction is enforced in the carrier attempt ledger: a
`interrupted_before_dispatch` receipt is retained for audit but does not close
the source, while a live interruption remains closed. Gear routes no longer
apply a duplicate source damage/critical budget; live own-health, Sanctuary,
identity, route, crowd, loss, and carrying gates remain authoritative.

Offline readiness inspection now shares the already-ranked hunt frontier with
gear analysis and uses a bounded `--max-analysis-seconds` budget. A cold source
parse or ranking timeout returns `analysis_status: "timed_out"`,
`analysis_complete: false`, and `live_authorization: false`; it is diagnostic
evidence, not a progression decision or a permission to start a connection.

## November 19 Architecture Checkpoint

Campaign checkpoint state now has an explicit runtime owner. The
`CampaignStateOwner` binds the mapping loaded from storage, the repaired mapping
handed to policy selection, and each mapping sent to a checkpoint. Its
`CampaignDecisionContext` owns derived selector caches and recursion limits.
This is a boundary contract, not a full-state copy: normal reads must remain
cheap, and durable evidence still belongs in SQLite. When adding a repair that
returns a replacement mapping, bind it at the next named lifecycle boundary and
cover that transition with a focused test.

## November 18 Architecture Checkpoint

Keep evidence reads separate from decisions. Protected-retry history is
loaded on demand after identifying a matching loss; do not read full past
segments merely to decide that a candidate has no loss. On checkpoint 84630
the old query returned 256 segments containing 72,293,227 JSON characters.
Only the selector with the actual search options should cache a hunt decision.
A miss with flight or Sanctuary ruled out is not a miss when they are allowed.
A search cut short by the deadline is not a completed search.

Check the linked run before reporting XP. Runs 25638–25649 together lost
1,290 XP in about 21 minutes of recorded segment time, **excluding** time
between segments and planning. The two most recent searches for Blacksail
accounted for 227 seconds of that time and zero XP. Checkpoint 84641 did
not open a connection. Do not count a supply kill, safe return, or a
planning-only checkpoint as a successful XP hunt.

The campaign now separates durable source evidence from transient decision
flags, caches source indexes within one decision, and keeps execution,
objective, and safety outcomes distinct. The latest live proof exposed one
remaining route-state flaw: after an armed transit crowd was seen, a generic
`look` could consume the bounded wait and let movement continue without a new
adjacent scan. The route controller now owns an exact `(route step, room,
direction)` retry token and reissues `scan` before it can advance. A mismatch
fails closed and preserves the route evidence.

The policy selector now has an explicit liveness handoff. If a same-state
source scan reaches its preparation budget at a safe healer checkpoint, the
next decision can use only an exact, already-audited Sanctuary carrier or
Moria recovery route. It records the original timeout as `handed_off` and does
not enter broad carrier rotation or repeat the full frontier scan. This keeps
maintenance and ordinary XP selection separate; a timeout is not treated as
proof that every target is absent.

If no exact maintenance owner is usable, the selector uses one healer-side
`world-time-probe` to create a fresh decision boundary. The probe preserves the
original timeout receipt and does not authorize combat. Broad source rotation
must wait for the following checkpoint rather than clearing the timeout inside
the same policy decision, and the existing six-hour probe cadence prevents an
immediate resume from reconnecting for the same liveness check.

Frontier diagnosis has the same ownership boundary. A complete diagnosis whose
boot, level, and source revision still match is retained through a preparation
timeout or planning-only recheck, and is marked with its selection stage and
outcome. Its source-catalog count is descriptive only; the executable-handoff
count and blocker list explain why no live segment was opened. An incomplete
scan is removed instead of being reported as evidence that the MUD is empty.

Gear preparation accepts a structured `equipment` snapshot when the derived
`campaign_worn_equipment` replay field is absent in an older checkpoint. An
explicit empty worn audit remains authoritative; only a fresh live `eq all`
observation can replace that evidence.

The resource owner also handles the known DD4 visibility edge. When an exact
charged Sanctuary staff was observed and then disappears from the inventory
row only because detect-invisibility expired, the same-boot, same-level,
no-loss receipt remains usable. A live inventory packet with detect-invisibility
active, a death or XP loss, or a boot/level change closes that receipt. This
prevents duplicate Moria resupply while retaining a real negative observation
when the object is genuinely gone.

The same ownership rule now covers flight preparation. When the exact prepared
source hunt reaches a terminal live absence, reconciliation consumes the
matching preparation receipt and leaves the source absence ledger available for
normal rotation. Older checkpoints may lack the `handoff_status` or candidate
cache; startup repairs those receipts from the exact saved mobile, room, boot,
level, and policy identity. A prepared flag is therefore never treated as a
fresh hunt, and an absent or maintenance-only segment is never counted as XP.

Live segment **25056** / run **25694** verified the legacy case: Dorrik was
safe at healer **3054**, but the exact Admiral Blacksail route was absent and
gave no XP. The persisted checkpoint still carries the old unbound marker; the
next resume must repair it before ordinary selection, rather than buying flight
or replaying the route.

Focused checks for this change pass. Do not count them as a second daily
regression batch.

## November 15 Carry-Capacity Fix

**81174/25155**: Dorrik is **level 46**, at **2,185,732 XP** with **75,268**
to level 47, safely back at healer **3054**. The latest bounded live segment
selected the Cyclops Torturer, released one exact duplicate enchanted prayer
bead at the healer, verified **39/40** carrying capacity, acquired the needed
light-blue flight potion, and completed the kill for **+4,140 XP**. There was
no death, flee loss, or XP rollback; the campaign is **ready** for its next
segment and HERO 100 remains unproved.

Two earlier full-inventory stops exposed a classification gap. A route that
fails before combat because the healer cannot free one required item slot is a
safe preparation result, not a combat failure. The campaign now records that
exact route as context-bound capacity evidence, keeps the segment ready, and
rotates to another source-ranked current-band route. This was live-verified by
the Lotus Temple stop at **81163**, the Cyclops stop at **81169**, and the
subsequent successful rotation at **81174**. The marker is not a reboot quota
or a loss closure; it clears when capacity, level, boot, or source revision
changes.

The cleanup selector now recognizes one safe additional case: an exact source
identified duplicate plain pill. It retains one copy and disposes of only the
duplicate after the healer-side drop, sacrifice, and inventory acknowledgements.
Focused tests were added and compile/diff checks pass. The November 15 daily
regression allowance was already spent on the recorded **169 passed / 5 failed**
batch, so no additional pytest batch was run. Publication remains deferred
until the recorded **9:02:42 PM NZST** retry window after the prior publication
failure.

## November 15 Latest Handoff

**81099/25142**: Dorrik **46**, **2,171,755 XP**, **89,245** to 47, healer
**3054**, 1,073/1,117 HP, safe and fully recovered after the latest Lotus Temple
kill. Runs **25128-25142** added **15,848 net XP** through six useful kills,
one safe nonproductive live-consider result, and the required flight,
invisibility, bank and purchase maintenance. No death or XP rollback occurred.
No owned worker remains. Goal active, HERO unproved. Use the ordinary command
with `--segments 1 --reset-retries 0 --max-segment-runtime 600 --progress` while
verifying edits; unchanged batches remain available after coherent live proof.

The flight handoff correction is now live-proven on both the long Freeport route
and the Lotus Temple route: a long hunt leaves the fresh potion carried, waits
at the healer for any short old effect to expire, then activates and confirms a
fresh reserve before departure. Focused regression cases were added and compile
cleanly, but remain unrun under the spent November 15 allowance. The daily
169-pass/5-fail batch remains the only batch for this date. Publication is still
deferred until **21:02:42 +13** because of the recorded prior failure.

The full resumed **25108-25125** block is **-25,206 net XP**, four useful kills
(13,151), four maintenance kills (680), one death (-38,987), flee loss (-50),
no level gain. Whole-session 3,658.61 elapsed seconds gives **-413.37 XP/minute**;
connected 1,925.70 gives -785.36. The final completed recovery summary and
checkpoint deltas agree; do not sum only the pre-death partial run results.
**25124** proved funded invisibility acquisition, not a completed field hunt.
Its inherited-objective summary remains an open reporting issue. Alchemist
**25121** acquired no resource; its historical achieved summary is not proof.

Current corrections compile and scoped whitespace checks pass. The active
combat cleanup correction now assigns 90 seconds for a live escape, 60 seconds
for an incapacitated death transition, and 25 seconds for ordinary cleanup; the
outer campaign watcher honors that same policy deadline. It is compiled but
not live-proved. New cases for
SQLite-row history, latest-versus-old absence, selected supply ownership,
ordinary field-abort ownership and fresh staff pickup are saved, unrun under
the spent daily 169-pass/5-fail allowance. One pre-connection SQLite-row format
failure was corrected; **25123-25125** then executed. No publication retry was
started; the recorded November 14 failure still bars retry before **21:02:42**.

## November 15 Death Recovery And Follow-Up

**25117/80957** retraced the long Egor route after two adjacent scripted-hazard
aborts. It reached Egor late, hit the 300-second boundary in combat, then lost
50 XP on a failed flee. The 25-second cleanup cap ended with room **17541**
still fighting, 328/1,099 HP. **25118** next connected in Purgatory after a
further **38,987 XP** loss. This is a failed escape, not a clean timeout.
The existing recovery controller found the corpse, issued `get all corpse`,
`enter portal`, `wear all`, and returned to healer **3054**. It woke to eat,
resumed sleeping and completed recovery at **80963**. Equipment was recovered.
The campaign loss total correctly increased from 666,704 to 705,691 across the
connection. The completed recovery summary also accounts for that loss;
the unfinished pre-death summary alone did not contain it.

The unchanged eight-trip batch **25114-25121** ended at **80978**, level **46**,
**2,152,218 XP**, full recovery, net **-38,557** from 80934. Alchemist **25121**
gave 380 maintenance XP but acquired no required object. Its old summary says
achieved; the research receipt explicitly says `required_object_acquired: false`.
Do not credit a staff or ready reserve from that run.

Saved corrections, compiled but not regression-tested under today's allowance:
- An ordinary source XP stop's adjacent field-hazard abort ends that trip;
  it no longer replays the full route from the healer inside the same visit.
  Cheap origin checks and required-loot/legacy retry behavior remain unchanged.
- Sanctuary staff maintenance requires this connection's fresh exact pickup;
  a worn empty namesake cannot fulfill it. Potion quantity behavior is unchanged.
- An explicit empty acquisition ledger makes a Sanctuary resupply not achieved,
  even if its carrier died. Positive receipts still use existing quantity checks.
- Removed the added final-handoff Sanctuary selector, which duplicated an
  already-selected supply route and could interrupt ready XP. Gear repair and
  the ordinary loss/resource controllers remain in charge.
- Absence comparison priority is limited to the latest completed ordinary
  source hunt; trying another target spends that rotation. Old absences are
  not permanent exclusions. Normalize SQLite rows before examining thin headers.

**25122/80984** could not afford preparation. **25123/80991** used the confirmed
bank reserve; **25124/80996** then bought invisibility potion **19021** for
**220 copper**, exact selector **#10071**, carried instance **#22608**, leaving
780 copper-equivalent. The marker and purchase receipt prove acquisition;
its not-achieved run summary is a separate inherited-objective reporting issue.
A fresh 600-second ordinary invocation is pursuing the funded hunt. Egor's
exact loss remains closed; do not retry him to test these fixes. Active-combat
shutdown after the finite cleanup allowance remains an open safety issue.

## November 15 Measured Hunt Rotation

**25109/80907** safely killed goblin visitor **20301/20319** for **3,771 XP**.
**25110/80914** safely killed Buddha **10728/10819** for **2,514 XP**. Both
returned to the healer; the Buddha trip carried no failed circuit members.
The next visit **25111/80921** immediately returned to that Buddha, found it
absent and gained zero XP. Its persisted efficiency receipt proves that an
old 1,250-XP/minute rate displaced independently selected Tabernacle
**39012/39015**. This was a comparison-priority defect, not an empty world.

Measured source challengers now defer when a different executable candidate
is selected and the challenger is in the existing post-kill rotation or has
a latest absence result. The ordinary selected target remains owned. Historical
success is preserved; a selected repeat, or a fresh fallback with no independent
alternative, still passes through the unchanged selector. There is no reboot
wait, permanent absence closure or new retry quota. New challenger/current/
no-alternative cases compile, unrun under the spent daily allowance. A fresh
invocation **25113/80934** selected Mayor **29126/29156**, not the absent
Buddha, with **zero circuit extras**. It killed Mayor for **3,177 XP**, returned
to the healer and finished objective achieved/safety safe. This live-proves
the corrected next dispatch and retention of that kill without a failed child;
it is not proof of a multi-kill circuit or every rotation branch.

At 10:36:13 AM, completed **25108-25113** total **+9,662 XP**: three useful
kills (9,462), two Moria maintenance kills (200), one empty visit, no combat
losses/deaths/levels. Whole-session 1,053.93 elapsed seconds gives **550.05
XP/minute**; connected 650.12 gives 891.72. Latest XP **2,190,775**, **70,225**
to 47. **25108** acquired purple potion 4050 again on segment 24471, preserving
new acquisition provenance without any reboot quota. **25112** replenished it
again after consumption. An unchanged eight-trip batch is now running; count
only completed evidence. Today's regression allowance remains spent.

## November 15 Circuit Loss Ownership

Completed boundary **80895/25107**: Dorrik level **46**, **2,181,113 XP**,
**79,887** to 47, healer **3054**, 1,063/1,117 HP, full mana/movement.
Mayor **29126/29156** died for **3,495 XP** after `quaff purple` and a fresh
live Sanctuary affect. Elken **29122/29158** then withdrew for **-860 XP**;
the run is objective achieved/safety loss, net **+2,635**, not a clean circuit.
No actual multi-kill circuit is proved. **25099** previously killed Mayor for
3,563 XP, with another follow-on loss. Across **25097-25107**, net **+1,942**,
two useful kills, no deaths/levels; 2,475.68 elapsed seconds gives **47.07
XP/minute**, including development and preparation. Connected 1,577.27 seconds
gives 73.87. Do not replace this whole-session rate with a single fight rate.

The saved dispatch included Elken and Heralt despite their current-level exact
losses. Circuit extras could borrow a primary selection's protection/retry
admission. `_source_ranked_circuit_member_has_loss` now blocks those peers both
in circuit selection and when assembling stops from an older saved circuit.
It checks current-level mobile loss across reset rooms plus registered singleton
aliases; it does not change the primary's separate approved-retry contract.
Actual saved 24470 evidence returns Mayor open, Elken/Heralt closed. New cases
compile but remain unrun under the spent daily allowance; live dispatch proof
is pending. Ordinary identity, consider, crowd, health and source gates remain.

## November 15 Missing Combat Pouch

The current continuation found a real missing preparation step: checkpoint
80855 carries a purple potion, but has no pouch or usable Sanctuary reserve.
Outfit run 25029 saw `[0 50] [#2252] a small leather pouch`, yet recorded
`no-legal-offer`. Five unrelated prototypes share that description; the
container classification itself was not the cause. Source `midgaard.are`
resets 3370 on leather worker 3010 in room 3035, with six armour basics.
The shop buys type 9 armour only, not type 15 pouches (shop row 5589).

Shop selection now narrows only pouch namesakes against that exact registered
shop's reset stock. An unknown/multiple shop or ambiguous remaining prototype
stays closed. Complete command-local listings, price and purchase replies,
class/slot checks and final equipment audit remain required. A new completed
outfit receipt records `shop_stock_identity_revision: 1`; the old false pouch
refusal receives one corrected visit, including at the final XP handoff.
The ground-fallback shortcut now requires usable, not merely carried,
Sanctuary. This does not require Sanctuary for ordinary admitted XP fights.
The attempted additional post-loss supply handoff was later removed because
it duplicated the normal supply owner; see the death-recovery follow-up above.
An actual reserve still prevents redundant acquisition. All changes compile; new tests
are saved but unrun under November 15's already-spent regression allowance.
Run **25104**, checkpoint **80877**, live-proved `buy #2252` for **50 copper**,
`wear pouch`, the exact purchase/wear replies and a filled final equipment
audit. Objective achieved, safety safe; no empty slots remain. **25105** used
the existing departure routine to `put all.purple pouch`, acknowledged the
transfer, and persisted one verified purple potion. It did not fight or gain
XP. No additional packing controller was needed; the speculative follow-up
change was removed after reading that transcript. **25106/80889** renewed
flight for **164 copper**, leaving **786 copper-equivalent** and usable
Sanctuary. **25107** subsequently proved its use in a real XP kill, although
the later failed child fight means the complete trip was not safety-safe.

Bank **25103/80872** deposited the old purse and withdrew one platinum;
the command-local balance reply left **127,141 copper-equivalent** banked.
Use fresh single-segment CLI invocations while changing decisions: a running
multi-segment process retains its imported code between trips.

## November 15 Circuit Preparation And Continuation

Checkpoint **80830/25096**: Dorrik level **46**, **2,179,171 XP**, **81,829** to
47, safely logged out at healer **3054**, full HP/mana and 624/648 movement.
No owned worker remains. Runs **25087-25096** gained **6,323 net XP**: Buddha
10728 kills **25090 (+3,784)** and **25093 (+3,995)**, partial net **+24** from
the failed 10727 fight **25095**, and **-1,480** from pirate guard 29129 in
**25096**. No deaths or levels. Both new exact current-level losses persist;
partial positive XP is not a kill or a successful encounter.

Elapsed 1,567.36 seconds including preparation/development gives **242.05 net
XP/minute**; connected 1,048.58 seconds gives 361.80. Across 25062-25096,
+13,721 over 8,005.13 elapsed seconds gives **102.84 XP/minute**. The earlier
individual fight rates are not the full-session rate.

The existing circuit builder rejected every special, including the already
source-audited `spec_cast_adept`. `special.c:556-645` stops it while fighting
and otherwise casts helpful spells. Circuit admission now permits only an
exact candidate/source match for this routine (or no special), preserving
mixed/unknown/dangerous special exclusion and all other live/source gates.
It uses the ordinary continuation threshold for adept-only stops. The two
actual prior Buddha records plus historical checkpoint 80769 now produce
10728/10819 then 10727/10820 stops with the existing 20% floors.

Measured selection can expand a winning singleton through the existing
builder from independently admitted measured peers, including a tied current
winner; existing circuits remain owned. Persist the member IDs and state
explicitly that the combined rate is unproved. Missing or neutral latest
results no longer erase durable achieved/safe visit proof; bounded summaries
must still prove it. Present negative consider, crowd, identity, route and
loss evidence stay closed. Verified histories may use the existing exhausted-
search repeat path, never a per-reboot quota or permission to clear a loss.

The final comparison also encountered an unbound generic policy template:
its actual candidate lived only in the compact record, before later dispatch
binding. It now reads that source-matched record and validates its own policy
ID; a mismatched named policy stays closed. **25093** emitted the measured-
winner message and killed its target: that final pre-gear branch is now live-
proved. Actual multi-stop execution remains **unproved**. **25095** subsequently
failed against 10727, closing this particular proposed pair at level 46.
Do not retry it to manufacture a circuit result; seek independent eligible
targets and keep 10728's separate evidence.

**25087** living shadow and **25089** Clive failed live consider, no combat.
**25088** renewed detection. **25091** returned for missing flight without a
fight; **25092** then persisted fresh `prepared` flight with duration 33.
Local teacher research found flamestrike 48 -> 52 at mage/cleric guildmasters,
cure serious 49 -> 53 and healing magiks 52 -> 54 at the cleric, using the
observed recovery stats. These are source practice estimates, not accepted
lessons or newly approved routes; three intellectual/zero physical practices
remain the audit. Current Knight targets consider the spell percentages
adequate, so evaluate marginal benefit before spending precious practices.

One broad line trace proved too expensive and was interrupted through its
owned tool handle (10174, exit 1); no external process was inspected or stopped.
Subsequent actual-checkpoint diagnostics used a 45-second subprocess bound and
completed. New circuit/ownership cases compile, unrun under the spent daily
allowance. Publication remains deferred until **21:02:42 +13**.

## November 15 Resume Ownership Repairs

Final boundary **80769/25086**: level **46**, **2,172,848 XP**, **88,152** to 47;
healer 3054, full HP/mana/movement, confirmed logout, no owned gameplay worker.
The independent Buddha **10727/10820** died for **4,075 XP**, objective
achieved/safety safe, 117.19 connected seconds. **25084** was likewise achieved
and safe, 168.28 seconds for 3,697 XP. The two adjacent prototypes are a useful
future circuit lead, not yet permission to combine visits or proof of a circuit.
The final pre-gear comparison ran without an error on 25086, but did not emit
its measured-winner branch; do not claim that branch live-proved.

Runs **25078-25086**: **+4,228 net XP**, two useful kills, one detect-hidden
maintenance kill, no deaths/levels. Ordinary hunt net +6,986; maintenance 130;
gear routes -2,898; another 10 XP on flight preparation remains unattributed
and is not credited as a kill. Elapsed 1,569.70 seconds gives **161.61 XP/min**;
connected 985.03 gives 257.54. Across 25062-25086, +7,398 over 6,087.31 elapsed
seconds gives only **72.92 XP/min**. Since 80582 net +13,860; since 80338 +6,334.
Keep Storn and both emerald-sword attempts' actual loss evidence. **25083**
lost 1,418 net, **25085** 1,480, neither acquired its object.

Open reporting issue: **25082** reports objective not_achieved even though its
buy/quaff replies and fresh fly affect prove the flight-preparation behavior.
Investigate its inherited hunt objective contract; never relabel the missing
Buddha kill achieved merely to repair the flight summary.

The continuation exposed three separate short-history problems, not a lack of
source targets. General selection could rename a failed named singleton;
embedded flight ownership fell out of the eight-run tail; measured source
wins also disappeared after unrelated maintenance.

The source-band gate now shares current-level/current-boot registered
singleton losses with the scout handoff. Keep the original receipt, and infer
no global identities for unknown or multi-target policies. Cache keys include
the registered ledger. Actual checkpoint **80719** now excludes Storn 19034
from its pre-existing named loss, without depending on the later generic
failure. The already-running **25079** still withdrew for **-786 XP**; that
new exact loss remains too. Next worker selected independent Teece 19069.

Flight lookup follows the saved owner through at most 256 thin headers and
one exact linked snapshot beyond eight recent snapshots. Missing/mismatched
newer ownership closes the lookup instead of restoring older standalone
success. Preparation and funding-resolution fields now survive campaign
boundaries. A confirmed purse increase covering the current-boot quote archives
the old funds-only delay in a resolution receipt and sets its active counter
to zero; independent shop-route blocks/cooldowns remain. **80729** resolves
failure **25072**, purse 101 to 1,001, quote 164, prior cooldown 3. **25082**
then actually bought/quaffed the light-blue potion. **80742** persists fresh
fly duration 32, `prepared` owner 25082 and the funding resolution; purse 837.
This live-proves bank-to-renewal, not only a selection flag.

`hunt_efficiency.load_bounded_hunt_visits` now links at most eight visits from
256 thin headers, reusing already-loaded snapshots and compact summaries.
Missing or mismatched evidence closes that rate comparison only. On real
80729 it recovers Buddha runs **25072/25071/25070/25068**, not just the latest
eight unrelated segments. The existing estimator excludes failed executions;
its 1,424 XP/minute winning rate therefore still measures 25068 alone. Keep
whole-session elapsed rates separate, including all preparation and failures.
The final ordinary-source handoff now runs measured comparison before optional
gear interception, including quick selector returns. Winner-only copy/binding
ownership and already-selected circuits remain intact. That final interception
change is saved/compiled; its own winning branch still needs live proof.

**25084** did recover the measured Buddha 10728/10819 through ordinary campaign
selection, stunned him, restored the primary and killed him for **3,697 XP**,
acquiring enchanted prayer beads. It fully recovered at healer checkpoint
**80756**, objective achieved/safety safe. Gear attempts **25083** and **25085**
acquired no emerald longsword: source carrier 29129 at 29169 then 29165;
the first encountered a duplicate pair. Keep their actual losses and scope.
The following **25086** is an independent ordinary Buddha 10727/10820 visit;
consult its terminal result before assuming any kill or launching a connection.

Source-only training review found positive intellectual practice gains at
teacher 31013 (base 35), but its 115-step route includes a large barracuda
crowd and a thief. Teacher 27337 (base 40) is 37 steps with water breathing
and economic-special route objections. No new training permission or lesson
is credited; distant higher-tier spell teachers still require their source
base levels. Three intellectual/zero physical practices remain the last audit.
All added cases compile but remain unrun under November 15's spent allowance.

## November 15 Productive Hunt And Flight Funding

Latest boundary **80715/25077**: level **46**, **2,168,620 XP**, **92,380** to
47; healer 3054, full 1117 HP/699 mana/648 movement, confirmed logout, no owned
worker. **25075** scouted Master Dunn, perfect-match consider, no combat.
**25076** stunned him, restored the primary weapon, used offensive spells,
kick and bounded healing, then withdrew for **-1,060 net XP**. Its current-level
registered loss is persisted (segment 24439). **25077** checked Secretary
30217/30256: "laughs at you mercilessly", so no fight. Return was achieved,
XP objective was not. It retained the banked platinum, purchase-failed false
and no funding marker: the funded-state handoff did not repeat a money trip.
It does not prove renewed flight or another productive Buddha visit.

The latest three-run batch is **-1,060 XP**, no kills/levels/deaths. The full
25062-25077 block is **+3,170 net XP** across **4,282.69 elapsed seconds**
including development/preparation: **44.41 XP/minute**; connected-only time
1,790.61 seconds gives 106.22 XP/minute. Neither is the isolated best fight's
rate. Since 80582 net +9,632; since 80338 net +2,106. Prior observations below
remain dated evidence, not this latest checkpoint. Next ordinary selection
must retain Dunn's loss and Secretary's negative consider, without inventing
a reboot wait or global empty frontier.

**25067** located the wandering Moria carrier in 4071, killed it for 90
maintenance XP and acquired purple potion 4050. **25068** then killed Golden
Buddha **10728/10819** for **3,654 XP**, objective achieved and safety safe:
153.93 connected seconds including travel/recovery, about **1,424 XP/minute**.
This is a different prototype from failed Buddha 10729. One win is not a
sustained progression loop. **25069** needlessly diverted into another gear
trip: route orca **17051** forced withdrawal for **-1,480 XP**; the planned
axe was not acquired. Retain that route loss without inventing an endpoint loss.
A stale-primary hint now yields to a selected productive hunt while its source
no-progress streak is zero; repeated unproductive hunts still trigger repair.

**25070-25072** could not afford inline flight renewal. The active policy now
owns a terminal preparation receipt even when the initial runner was an XP
hunt, not a standalone potion request. Shared terminal snapshots carry typed
failure or fresh-effect completion, scoped to run, level and boot. The latest
owner wins; inherited markers are not attempts, and malformed newer ownership
cannot restore an old success. Bound embedded reads to eight snapshots; legacy
repair uses fewer than 256 SQL-filtered command/response rows, unchanged
character/level/boot/XP and the exact failed purchase plus safe healer endpoint.
The live failures **25071/25072** prove failure persistence, not successful
renewal. Fly duration zero is still active until its removal tick, but does
not meet the requested departure reserve; it must not erase a funding task.

The normal selector then chose the confirmed-bank workflow. **25073** withdrew
one platinum, leaving **1,000 copper-equivalent** in the purse. A stale purchase
cooldown nevertheless sent **25074** on unnecessary funding work. It found
Valan below band, stalled on return recalls, then reached the healer and
confirmed logout: checkpoint **80701**, level **46**, **2,169,680 XP**, **91,320**
to 47. Its outcome is failed/not_achieved/safe, not progression. The funds
repair now recognizes a newer purse increase covering the current-boot quote
before the old cooldown can demand more coins. Preserve the refusal and
cooldown as history; unknown/stale prices and carrying failures do not qualify.
Read-only inspection of actual bank checkpoint 80696 returned purchase-failed
false. Full bank-to-renewal-to-repeat success still needs live proof.

Since checkpoint **80644**, net **+4,230 XP**: ordinary-hunt net 5,370,
maintenance 90, gear-route net -1,230. The wider block since **80338** is now
**+3,166 XP**. No level gained or death in this continuation. New cases compile
but remain unrun: November 15's 169-pass/5-fail batch is spent. No publication
attempt before **21:02:42 +13**. Current ordinary continuation owns any later
worker; consult its terminal checkpoint before launching another connection.

## November 15 Visibility Cleanup Ownership

**25062** restocked food. **25063** withdrew from Golden Buddha **10729/10818**:
3,196 damage XP minus 1,480 flee penalty, **+1,716 net**, no kill. Keep its
exact loss; positive partial XP is not an achieved hunt. It exhausted eight
self-heal attempts while 489 mana remained at escape. That is an optimization
lead, not permission to change existing combat timing or healing limits.
**25064** renewed flight. **25065** killed stone golem **5208** for **250 XP**;
it acquired and wore a **mithril helm**, but not planned vest **5200/5247**.
The gear objective correctly remains **not_achieved**; no vest credit is due.

**25066** bought/activated detect invisibility and returned to healer **3054**,
then stalled without a logout command. The 45-second watchdog closed the
connection safely and recorded failure at **80666**: level 46, **2,167,416 XP**,
**93,584** to 47. Its capacity cleanup had dropped one surplus pie, but issued
neither sacrifice nor the confirming inventory. The visibility potion-capacity
helper saw the fresh free-slot count and marked cleanup complete, leaving an
acknowledged drop reply pending; the final completion guard then waited on it.

That helper now yields to the recovery-owned cleanup controller whenever its
reply is pending. It must finish the complete drop/sacrifice/inventory cycle
before the free-slot shortcut applies. The saved case covers a split drop
reply, ownership through the new GMCP free slot, and both later confirmations
without extending the original one-disposal budget. It compiles, **unrun**;
new live reproduction remains unproved. Normal campaign continuation restarted
after saving this correction. No extra regression or publication attempt ran.

## November 15 Relative-Level Floor Repair

The wolf-pack lead exposed a conflicting final gate. On real checkpoint
**80644**, source/catalog/navigation checks all retained wolf pack
**17053/17276**, and `_source_ranked_relative_level_target_admission_allowed`
approved it. `_source_ranked_candidate_in_current_band_uncached` nevertheless
rejected it because nominal level 41 was five below the level-46 pilot, despite
its useful upper fuzz levels. A bounded trace located this exact rejection;
there was no preparation timeout or new live connection during diagnosis.

That old nominal-floor branch now honors the already-proved relative-level
contract, as its later band check already did. Ordinary aggression alone and
the possibility of a low-XP load are not hard source hazards. Existing source
special/script/population/route exclusions, observed identity, live `consider`,
own-health and exact loss checks remain. Repeating the read-only selector on
80644 now returns that exact wolf pack. This is selection evidence only, not
a completed ordinary hunt or permission to reuse the failed pirate carrier.
The renamed/expanded floor test compiles but remains unrun under November 15's
spent allowance. Normal live continuation restarted with food restocking.

## November 15 Latest Continuation

Checkpoint **80644**, run **25061**, leaves Dorrik level **46**, **2,165,450 XP**,
**95,550** short of 47, at healer **3054**: 1068/1117 HP, full mana/movement.
Since 80582, net **+6,462 XP**: 2,536 ordinary-hunt net, 750 Sanctuary
maintenance and 3,176 gear-route net. One ordinary objective kill and two
incidental gear-route kills; no deaths or level gains. The wider block since
80338 is still **1,064 XP down**, not a proven sustained progression loop.

**25057** withdrew from Ares 906/938 for **-887 net XP**. **25058** acquired a
fresh ivory staff after killing the Alchemist for **390 maintenance XP**.
**25059** rejected below-band Hermes and returned without combat. **25060**
withdrew from the Tabernacle target 39011/39014 for **-360 XP**. Their exact
losses remain closed. The gear handoff then actually dispatched **25061**
with the updated selector, choosing Frostbite **17063**, carrier **17069** at
**17299**, rather than the earlier diagnostic vest. It killed orca **17051**
for 390 and wolf pack **17053** for **3,336**, then withdrew from the carrier
for a net 550 penalty. Net trip **+3,176**, **268.98 seconds**, but objective
**not_achieved** and safety **loss**: no sword acquisition or upgrade credited.
Confirmed logout completed at the healer; no owned gameplay worker remains.

Next: examine wolf pack 17053/17276 as an ordinary XP target independently of
the failed pirate. Source level **41**, fuzz **39..43**, one effective reset,
no special or equipped reset, no hard route hazard in the raw source ranking.
The long source-ranked route includes the orca; this needs the normal
route/return, identity, live `consider`, actual crowd and own-health checks.
The gear trip's safe wolf kill is research evidence, not a successful ordinary
visit summary, retry permission, or reason to erase the pirate loss.

November 15's failed 169-pass/5-fail regression batch remains the only batch;
new cases compile but are unrun. Publication remains deferred until
**21:02:42 +13**, following the recorded 24-hour failed-attempt delay.

## November 15 Equipment Mode Fallback

Read-only selection on real checkpoint **80621** returned no gear because
the balanced search preferred recovery and never tried combat afterward.
The selector now searches the other stance once only when the first has no
executable upgrade. Existing source route, item, carrying, exact attempt and
loss gates run for both modes. A preferred winner keeps its turn.
The same checkpoint now selects **mithril vest 5200**, stone golem **5208** at
**5247**, combat stance, through the existing Thalos route contract. This is
source-selection evidence only, **not acquisition or an observed damage gain**.
The gear path also rejected carriers after three kills per reboot, closing
uncollected items merely because earlier items shared the carrier. That quota
is removed. Repeating the read-only selection with **all four actual current-
boot stone-golem kills loaded** still selects the vest. Exact failed item
placements, live checks and saved losses remain enforced. A new parameterized
carrier case keeps the selected item eligible at 0/3/30 prior kills and still
rejects its exact attempted placement; it is saved, compiled and unrun.
The focused fallback cases compile but remain unrun; no extra daily regression
batch was launched. **25057** meanwhile withdrew from Ares 906/938; preserve
that exact loss rather than repeatedly attacking him.

## November 15 Resource Completion Repair

Run **25049** killed Wei Chin for **4,739 XP**, but its ivory staff explicitly
blazed and disappeared. A later checkpoint still inherited the old two-charge
record: normal completion omitted an empty ledger, unlike runtime interruption.
Both normal completion boundaries now emit an explicit empty mapping when an
authenticated run has observed inventory and owns inherited resources. An
unobserved or pre-login inventory cannot clear those inherited receipts.
The first live check **25054** exposed an additional ownership boundary:
confirmed logout clears authentication before normal snapshots. The condition
now accepts that same session's confirmed logout plus observed inventory;
logout alone is insufficient. Run **25055**, ordinary liquidation, then
persisted an explicit empty terminal ledger and checkpoint **80620** retained
it. This live-proves clearing the inherited consumed resource after confirmed
logout, not every same-run acquisition/charge edge case.
Same-run acquisition fallback no longer replaces decremented charges or
restores consumed objects; an independent planned resource remains intact.
The existing confirmed-active flight receipt is preserved. Focused ownership,
consumption, receiver-merge and flight cases are saved and compile, **unrun**
under the spent November 15 regression allowance.

The following **25051** Wei Chin attempt withdrew for **-375 XP**; that exact
current-level loss remains closed despite the earlier wins. **25052** killed
Hephaestus for **360 maintenance XP** and acquired nectar. **25053** prepared
see-invisible. Checkpoint **80607** therefore records **2,163,712 XP**, **97,288**
to 47: **+4,724** since 80582, one useful kill and no deaths. The wider block
since 80338 is still **2,802 XP down**. Nectar acquisition superseded the stale
staff; that alone is not proof of the explicit-empty completion repair.
**25054** activated the nectar and fought Apollo 905/926 to the ordinary
withdrawal floor, using kick, flamestrike and cure serious. It escaped for
**-581 XP**, no kill or death, and fully recovered at the healer. Preserve
Apollo's exact current-level loss. Checkpoint **80620** is **2,163,131 XP**,
**97,869** to 47; the wider block since 80338 is **3,383 XP down**.

## November 15 Recovery And Equipment Work

Earlier checkpoint **80582**: level **46**, **2,158,988 XP**, **102,012** to 47,
healer **3054**, 1117/1117 HP, 699/699 mana and 641/648 movement. Continuation
since 80556 gained **5,309 net XP** (380 maintenance), one useful kill, no deaths.
Run **25043** selected measured dwarf 20514/20530 over unmeasured Olympus
905/926 using receipt 25042's **1,294 XP/minute**, proving the different-winner
handoff. That attempt withdrew for **104 net partial XP**, no kill, and now
closes the dwarf. Do not mistake the selection proof for combat success.
**25044** found no Moria resource; **25045** renewed flight. **25046** killed
the Alchemist for **380 maintenance XP** and acquired staff 905. **25047**
then killed Wei Chin 10732/10830 for **4,825 XP**, safe, with no Wu Tak stop.
The run took **200.17 seconds** including connected travel/recovery, about
**1,446 XP/minute**. **25048** sold spare loot and ended safely at the healer.

`self_buffs.py` now owns bounded learned-protection preparation through the
recovery session. Initial support is source-audited `armor`, observed positive
practice, on Mage/Cleric/Knight paths. `const.c` gives minimum mana 5 and one
wait pulse; `handler.c:mana_cost` supplies the proficiency-dependent cost;
`spell_armor` gives AC -20. The controller keeps the mana reserve, half-second
source wait/input allowance, exact complete reply and fresh affect revision.
One cast and a 12-second deadline bound it. It never refreshes active armor,
sleeps/wakes for this optional spell, claims NPC chatter as its own cast, or
changes combat admission. Missing prompts stay transport-owned; interrupted
scopes cancel preparation without holding emergency recovery.

The first live check **25046** persisted an idle receipt: a direct shop handoff
bypassed the initial hook. Moving the hook to the real fastwalk departure
boundary fixed that ownership gap. **25047** persisted `status=active`, armor
99%, zero attempts: no-refresh and receipt capture are live-proved. An actual
missing-armor cast, reply failures/deadlines and interruption paths are saved
as focused cases and compile, but remain unrun/unproved. No extra regression
batch was started. The wider block since 80338 remains **7,526 XP down**.

Latest continuation **80503 -> 80556**: Dorrik remains level **46**, with
**2,153,679 XP**, **107,321** short of 47, fully recovered and logged out at
healer **3054**. Net **+10,129 XP**, including 370 maintenance XP; three useful
kills, no deaths. **25032** killed Wei Chin for 5,268, then escaped Wu Tak at
74 HP; net **+4,914**, safety loss. The same-room combat-recall prompt returned
immediately to flee rather than waiting. **25034** killed dwarf 20514/20530
for **2,755**, safe; **25042** repeated for **3,714**, safe. **25035** withdrew
from croupier 30209/30207 for **-712**. Those losses retain exact identities.

The early scouting-to-XP handoff bypassed the existing measured-route comparison.
It now compares eligible source hunts without replacing a selected circuit.
Each alternative uses copied state; only the winner commits its candidate,
circuit and retry binding. A rejected comparison cannot rename dispatch.
The dwarf receipt also disappeared after an unrelated loss lowered current XP
below its old end state. `completed_single_target_hunt()` now permits only the
decline covered by the increase in cumulative recorded XP loss, preserving
the encounter's unchanged loss total and all exact target/source/boot/level
checks. Real saved data from 25034 is recognized again; 25042 invoked the
comparison and retained/completed the dwarf route. A different measured winner
has not yet been live-proved. Added regression cases are saved/compiled only.

**25037** failed visibility preparation. **25038** then used the confirmed
bank reserve automatically; **25039** bought/confirmed detection, killed
Hephaestus 908/937 and acquired nectar 926 for **370 maintenance XP**.
**25040** made an empty trip when `eat nectar` returned too full. A required
pill now makes its first bounded activation check at the healer when observed
fullness exceeds `max_hunger - 5`, matching `do_eat`; fresh pills that fit
remain for the endpoint. Actual refusal/effect replies and the existing
cooldown remain mandatory. **25041** sent no nectar command during that
cooldown and lost **912 XP** fighting the sand worm without protection. Its
exact current-level loss remains closed. The new first-fullness healer branch
is not yet live-proved. One logged status overstated a healer retry; the next
record explicitly corrected it. No protection activation is credited there.

The wider block since 80338 remains **12,835 XP down**. Keep whole-session
losses visible rather than reporting only the latest winning hunt.

Runs 25014/25015 and 25019/25020 repeated no-sale liquidation. Retained-item
receipts now retain source hints and stop an unchanged capacity keyword from
forcing another identical visit. Actual identity changes remain auditable.
The urgent no-food handoff reused a confirmed bank reserve in **25016**:
one platinum withdrawn, **130,775 copper-equivalent** remained banked, followed
by food restocking in **25017**. This proves that workflow, not every visibility
funding path.

Run **25018** exhausted its command budget cycling around a failed flight
purchase/carrying preparation. Failed purchases now finish their return route
and end preparation at the healer; fresh renewals reset their capacity owner.
Verified city-shop movement checks retain combat gear rather than reducing
capacity mid-route. **25021** proved purchase, flight confirmation and onward
travel, not all failure/retry branches.

A historical two-attempt Sanctuary counter had invented a fatal Moria route
failure. The selector now archives only that synthetic failure and preserves
actual terminal evidence. **25022** subsequently killed mobile **4055** at
**4064**, acquired purple potion **4050**, and returned safely: **90 maintenance
XP**, not a current-band hunt. Dynamic visibility also binds the selected
carrier rather than generic inherited VNUMs; its hidden-carrier path remains
unproved.

Run **25024** used the potion against **Odin 914/929** after verified detection.
Several flee attempts failed, Sanctuary expired, and poison/melee killed
Dorrik. Net XP: **-24,947**, no kill. His frost breath also destroyed the small
leather pouch. Corpse recovery, equipment recovery and healer return completed;
the exact loss remains closed. Do not report this as successful progression.

Actual checkpoint **80473** then exposed a separate global gear cap: five
combat and five recovery attempts prevented even checking an untried item.
Removed that global per-level/boot quota, retaining exact placement/plan
history, live gates and the gear/protection XP-turn handoffs. Post-loss final
handoff can now inspect gear before another supply trip. **25025 / 80477**
collected **large club 1521** from ground reset **1573** and returned safely.
Acquisition left XP at **2,137,948**, level **46**. The following Moria visit
**25026** acquired nothing; **25027** renewed flight. In **25028**, Dorrik
wielded the club, successfully stunned the Alchemist **916/927**, switched
back to the bishop-piece primary, killed him for **400 maintenance XP**, and
picked up/held ivory staff **905**. Successful stun and the weapon switch now
have command-local live proof. This is not a useful-band XP hunt or proof of
better whole-session XP/minute. No staff charge count is live-verified merely
by its source prototype or acquisition.

After one unsuccessful pouch-outfit visit (**25029**), the normal selector
gave the prepared gear an ordinary hunt rather than another optional upgrade.
**25030** acquired an inky black detect-hidden potion from goblin **4520**
(130 maintenance XP). **25031** activated the ivory staff, killed sand worm
**39004** for **4,633 XP**, then continued to a dust dweller in room **39009**. The latter
fight ended in a health/command-lag withdrawal, not a kill. Net for the hunt:
**+5,072 XP**, including partial-combat XP and escape cost. Preserve that
failed second encounter even though the overall XP balance is positive.
The exact loss is mobile **39008**, room **39009**, not the sand worm.
Checkpoint **80503** is level **46**, **2,143,550 XP**, fully recovered and
logged out at healer **3054**. **117,450 XP** remains to 47. Run duration was
**287.75 seconds**, about **1,058 net XP/minute** including its travel/recovery
but excluding earlier supply/gear visits and source selection. The wider block
since 80338 remains **22,964 XP down**; one positive hunt is not sustained
progression proof. Recorded outcomes are success/achieved/loss, not all-safe.

The charge-count discrepancy is explained by `server/src/db.c`:
`create_object()` applies `number_fuzzy(value[1])` to an ordinary staff and
copies that result into `value[2]`. `number_fuzzy()` varies by -1/0/+1 with a
minimum of one. The ivory prototype's three charges therefore load as two to
four; its two observed activations followed by disappearance are consistent.
Complete-heal staves have their separate source rule. Do not treat source
prototype counts as a live identification or invent a remaining charge after
observed disappearance. The live loss of the staff is handled normally.

November 15's recorded batch remains **169 passed, five failed**. Corrections
and follow-up cases are saved/compiled, not rerun; no second batch is allowed.
Publication remains deferred until **November 15, 9:02:42 PM Pacific/Auckland**
under the recorded failed-attempt delay. No remote operation was attempted.

## Search And Dispatch Ownership

Moria runs 25006/25007 returned without a carrier kill. A positive locator
was followed by an orc-only room; the refreshed route then chose snake room
4058 despite having alternatives. Required-loot sweeps now retain absent
carrier searches past identified low-band bystanders without inventing
presence. Refreshed selection audits at most 32 registered paths, records at
most eight rejected paths, and chooses a clear alternative. Existing source,
live movement, combat, poison and return gates remain unchanged. These new
cases compile but have not been regression-tested or live-proved.

Failed visibility preparation in 25008/25009/25012 exposed lost policy-owned
shop facts. The shared terminal snapshot now retains the failed attempt's
quote, stock, purse, boot, level and actual verification outcome. When an
independently selected hidden carrier needs that unaffordable potion, the
existing funding/bank controller takes precedence at a recovered healer.
Run 25009 proves receipt persistence, not successful funding or purchase.
The receipt now also survives intervening maintenance; boot/level, actual
selected need and affordability still govern any later funding handoff.

Run 25010 announced Caerlin but silently dispatched Moria, killed mobile 4055
and acquired purple potion 4050. The object and 100 maintenance XP are real;
the Caerlin acquisition/objective credit is false. Dynamic dispatch now rejects
a missing/mismatched binding or failed contract rather than silently replacing
the carrier. A fresh exact source-audited Caerlin may retain its selected
route without using an obsolete generic preparation marker; all losses and
live gates remain. Bounded correction uses 256 thin headers, at most eight
projections and compact run summaries to flag mislabelled acquisitions. It
preserves the original claim and actual inventory and prevents that segment's
historical repair from recreating success. Old run outcomes remain historical
and must be read with this correction. The receipt flag persisted before 25011;
the false research credit is absent at checkpoint 80428, with the invalidated
receipt retained. Fresh dynamic Caerlin dispatch still lacks live proof.

Run 25011 used the real purple potion and fought King Loranhir. Energy drain
removed health/mana and XP; the visit ended without a kill, 1,509 net XP down.
This is a retained combat failure, not progression success. The pilot returned
to healer 3054. Run 25013 ended without combat or its supply objective;
checkpoint 80428 is fully recovered, level 46, 2,162,805 XP, without Sanctuary.
The block since 80338 is 3,709 net XP down. New tests are saved/compiled only under the spent November 15
allowance. No repeat regression or publication attempt is permitted yet.

## Prepared Progression Follow-Through

Run 25001 now passed the source-approved mage status gate, but its nectar
activation received `You are too full to eat more.` No Sanctuary or kill was
credited. A command-local pill refusal now retains the object and records a
five-minute activation wait across reconnects; it cannot count as usable
protection during that interval. Afterward, a needed retry occurs at healer
3054 before travel and still requires actual effect confirmation. Time passing
is retry permission, not proof of digestion or a spell effect. Other usable
resources remain eligible; no reboot quota or permanent item ban is created.
New cases compile and remain unrun under the daily allowance.

Runs 24993-24995 renewed flight, acquired detect-hidden potion 4558 and reached
the intended dust-dweller circuit. The potion was used for that hidden target,
not unrelated gear. The fight ended in withdrawal for 66 net XP lost. Athena
24996 also withdrew; Hephaestus 24997 supplied Sanctuary nectar 926, not a
staff. These are concrete failures/preparation, not completed XP hunts.

Run 24998 showed optional gear priority intercepting a newly prepared XP turn.
Fixed and dynamic Sanctuary acquisitions now share segment-ID provenance;
both optional-gear handoffs retain a confirmed usable acquisition's real
combat opportunity. The bounded legacy repair reads 256 headers and at most
eight projections, requiring this exact visit's acquired VNUM and matching
retained resource for old fixed policies. It never restores combat permission
or deletes losses. Up to eight compact summaries within 32 visits distinguish
actual ordinary combat from supply/empty/in-flight visits. Saved cases compile
but remain unrun under November 15's spent allowance.

Moria conversion `086825c` is newer than the live deployment. Its exact carrier
4055 now uses the audited pre-conversion record at
`4f0d46ebb7c9465571816e8476298577dc541eb3`: level 10, flags 68/0, alignment -500,
and legacy zero HP/damage/critical/swiftness modifiers. No other Moria template
is restored. Real checkpoint 80352 now selects the ordinary required-loot
route to 4064/potion 4050; population and live checks remain mandatory. This
is source-selection proof, not yet a new live pickup or regression pass.
The normal maintenance fallback now checks that existing preferred Moria
selector after a usable proven carrier and before harder fixed Olympus
carriers. Its exact loss and research checks still apply. This restores the
intended low-level supply priority; it is not a broader fight permission or
a way around an exact carrier failure.

Poseidon 24999 passed live consider but stopped because the planner's approved
healer-return proof was not honored by the live blindness gate.
`SourceHealerRecovery` now carries that existing proof as exact mobile, room,
special, level ceiling and effect set. The live stop must still opt in, be
isolated/exact and remain recallable. Other casters, changed scope and psionics
do not match. Added cases are saved/compiled; a fresh live run must prove the
handoff before reporting a successful fight.
Run 25002 subsequently ate nectar, confirmed Sanctuary and entered combat,
live-proving the corrected handoff. It withdrew for 1,184 net XP lost without
a kill; that failure is retained. The fullness-refusal wait remains a separate
saved feature, not live-proved by this successful activation.

## Field Readiness And Required-Loot Handoffs

Run 24990 aborted before combat because the saved `2.dragonorb` keyword no
longer matched its single carried orb. Resource commands now rebind to the
current unique source-matched inventory instance: prefer a fresh TARGETMODE
selector, otherwise prove a source word has no possible carried prefix
collision. Unknown inventory, duplicate instances and ambiguous source names
do not justify a guessed ordinal. The durable record is not rewritten into
an ephemeral selector. New cases compile but have not been run.
Run 24991 then proved the fresh `dragonorb` reference reached the correct
object, but live alignment 515 rejected it. Campaign selection now refreshes
held-resource class/alignment usability and both protection predicates reject
an explicitly unusable reserve. Live activation repeats the source legality
check. A hold followed by a zap/drop is failure, not success, and a nonweapon
drop no longer invents a weapon disarm. Only the stale-selector repair has
live proof; these additional cases are compiled and saved unrun.
The live `I see no bishop here.` refusal is now an explicit failed pickup,
rather than leaving weapon recovery pending for the whole worker deadline.
Run 24991 reached its configured runtime limit; the next ordinary campaign
invocation selected return-home and reached healer 3054 in run 24992.

An unsuccessful optional gear trip now yields to the next executable ordinary
XP visit rather than chaining more equipment searches. This is separate from
an acquired upgrade's stronger useful-combat proof. Neither an in-flight visit
nor a source-ranked Sanctuary maintenance hunt consumes either XP turn.
The new cases compile and remain unrun under today's regression allowance.

Run 24982 exposed premature potion use: the new sword's visible carrier did
not require the inky black potion, but generic healer preparation consumed it.
Inline detect-hidden activation now requires a remaining source-hidden stop
and an outbound trip. Unrelated gear/supply work and completed returns retain
the reserve; the explicit standalone activation path is unchanged. New cases
are saved and compiled, not executed under the spent daily allowance.

Standing field healing is recovery-controller-owned and scoped to room,
level, boot and selected source stop. A fresh complete room inspection and
source route audit precede casts; every self-heal needs its own acknowledgement
and full source lag. Limits are eight casts, 45 seconds, eight contexts per
run and a retained mana reserve. Hazards or changed identity end the attempt;
existing health readiness and combat withdrawal floors stay unchanged.
This is not sleeping outside the healer. New cases compile but remain unrun;
field recovery has not yet been demonstrated live.

Recovery acquisition now requires a positive marginal HP/mana resource rank
in the class's priority order. Pure combat, stat or armor tie breakers cannot
send the pilot on a sleeping-gear expedition. Actual wearing and combat
acquisition retain their existing separate rules.

Run 24979 killed the potion carrier, then fled from Essabella despite full
health, losing 1,480 XP. Source `spec_guard` and the live attack text confirm
she really joined; this is not a GMCP correction. The required-loot controller
already admitted her bounded low-guard loadout and fresh exact-instance easy
consider, but the identity-mismatch branch pre-empted post-kill adoption.
That handoff now runs first for one raw enemy only, after the exact carrier
kill and with matching source identity, receipt, room, level and boot.
`campaign_required_loot_guard_handoffs` records bounded diagnostic receipts.
Unknown opponents and other specials remain closed; losses are never erased.
Saved regression cases compile but are unrun, and this handoff is not yet
live-proved. Run 24981 separately acquired the inky black detection potion.

## Compact Combat Evidence

`run_combat_metrics` stores observed combat-entry and decision counts with the
canonical event transaction, including the bounded writer path. Enemy-stream
and textual starts are deduplicated while engaged; malformed enemy packets do
not clear engagement. One row is initialized when a run is created, so reopen
and compact-summary generation do not scan historical events. Mid-history
collection is partial, never upgraded to complete by a later packet. Older
compact reports show known minima and unknown decisions rather than claiming
no combat. Existing objective and safety outcomes remain independent.
The new cases are saved and compiled, not run under November 15's spent
regression allowance. Do not backfill the entire production database.

## Local No-Recall Returns

Gear run 24970 reached room 17299 after a route fight and could not complete
its recall-only return. The separate recovery 24971 reached healer 3054 but
lost 1,480 XP after following a long graph path. The existing bounded local
escape finder proves `up` to 17278 while flying. Both recall-only fastwalk
returns and ordinary recovery now use that checked escape followed by recall
and the ordinary live healer waypoint before a long path. Do not append a
blind north command before confirming where recall actually arrived.
Preserve explicit direct return commands,
source hazard audits, current movement capabilities and combat withdrawal
priority. Missing flight is not assumed, and this never reopens the failed
gear route. The dispatcher changes compile; new cases are saved unrun and
this shorter recovery has not yet been live-proved.

## Current Target-Selection Policy

### Ownership Of Unlaunched Absence Handoffs

A pre-dispatch source-absence marker is an active selection reservation, not
evidence that a live locate occurred. If final selection binds a different
exact source policy before a segment opens, restore the saved absence result
and clear only the reservation. A segment-start receipt owns dispatched retry
history; an abandoned reservation must not erase research evidence or reopen
the same full source scan on the next invocation.

### Loadout Repair And Perception Timing

Run 24969 proved combined preparation: buy/consume the verified see-invisible
potion despite already-active flight, continue to Athena, defeat her and
acquire the ivory staff. Its source prototype lists three charges, but the
live staff disappeared after two observed activations in 24970; that source
count is not proof of the acquired object's remaining charges.
Runs 24967/24968 exposed the old bug:
flight completion bypassed the separate detection requirement. Flight may no
longer release the shop controller while requested detection or breathing is
unverified. Purchase failure, carrying, source route and live detection gates
remain intact.

Source refresh used to erase the sewer-dragon acquisition preference with its
derived research results. `campaign_sanctuary_carrier_acquisitions` now retains
32 actual acquisition receipts with original source revision and segment ID.
The bounded legacy repair reads 256 thin headers and at most eight related
projections once per boot/source context. It restores ranking provenance only,
not research permission or losses. Checkpoint 80245's read-only reconstruction
recovers acquisition 24305; the current source audit selects 7040/7428/7303.
The persisted repair is present in checkpoint 80250. New cases compile but
remain unrun under today's spent regression allowance.
Runs 24976 and 24985 subsequently reacquired the same source carrier's object
at the same level and boot, live-proving repeated replenishment after refresh.
Prototype charge counts are not live remaining-charge measurements.

An exact retained detect-hidden potion can satisfy a preparation plan without
a separate return-home segment. Validate the unique source object, activation,
positive charge count and current inventory description; do not turn an unknown
or ambiguous ledger row into permission. A copied planning view may represent
the pending preparation, but the saved live affects remain unchanged. The
existing healer controller owns quaffing and observed-effect confirmation.
Run 24946 proves activation followed by onward travel in the same session;
it remains a scouting visit, not an XP kill.

At a recovered, provisioned healer checkpoint, the four registered chess-dwarf,
Storn, gambler and Master Dunn scouting policies now first offer the ordinary
source-ranked selector a chance to find an executable XP hunt. This happens
before target-specific detection preparation. Adopt its exact candidate and
any circuit only when selected; discard speculative state changes on a miss.
No target admission, loss closure, live consider, source-reset or combat rule
is widened. Negative fame, active quests and QP shortfalls keep their own work.
When no ordinary hunt is executable, preserve the original scouting route.
Run 24951 selected the ordinary dwarf hunt and achieved 4,865 net XP safely.
Run 24950 exposed a registered/generic gambler alias after a recorded loss;
the optional handoff now excludes reset-policy aliases of exact registered
singleton failures. This does not invent identity for ambiguous route losses.
The November 15 focused batch passed 169 cases and failed five. Corrections
are saved and compile, but have not been rerun; today's allowance is spent.

After at least two current-level losses and either a stale primary weapon or
two trailing unproductive source hunts, the final campaign handoff may
prioritize one executable gear upgrade. Count distinct failed segments across
registered and generic policies, not just one target's largest loss counter.
This includes early-return
hunt selections. Preserve quest/QP, healer readiness, provisioning, carrying,
source carrier, route and exact-loss checks. A preceding gear policy gets a
hunt before another handoff; the existing bounded gear controller owns the
actual acquisition. A better source score is not a completed upgrade.
Runs 24953, 24955 and 24958 acquired mithril gauntlets (5202), a mithril girth
(5206) and mithril sleeves (5203). A following liquidation visit exposed that `campaign_last_policy`
does not identify the latest gear acquisition. The priority rule now reads
the acquired-object receipt, at most 32 latest completed hunt headers and
eight compact summaries. Require a useful source-tagged objective kill,
combat beyond incidental route kills or an XP-losing attempt: empty,
below-band and setup visits do not test gear. Partial-combat XP is not a kill.
An explicit safety-loss outcome also counts as an attempted fight even when
partial XP leaves a positive balance, as run 24960 demonstrated.
Maintenance cannot erase the upgrade's pending XP turn. Those additional
cases are saved and compiled, not run under today's spent allowance.

`GearSourcePlacement.upgrade_rank` records marginal stance benefit over the
selected replaceable slot, accounting for carried alternatives and paired-slot
capacity. Acquisition ordering uses it before standalone `stance_rank`, keeping
status and weapon-role ordering. Combat compares generated weapon range plus
twice damroll on the same scale for every slot; hitroll/swiftness/critical
penalties remain signed. This is a ranking estimate, not actual damage or target
admission. Full-set bonuses and live randomisation are not marginal item proof;
the existing set-aware wear planner and live equipment checks still own swaps.
Read-only inspection of checkpoint 80103 changes the selected acquisition from
the helmsman's battle axe to mithril gauntlets (5202), subsequently acquired
and worn in run 24953.
The CLI exposes both ranks. Equipment ranking and the new gear-priority cases
passed in the November 15 focused batch; that batch failed elsewhere.

Run 24928's Cyclops-thief visit did not prove absence: detect invisibility
expired during travel despite detect hidden remaining active. Departure
preparation now requires at least two observed ticks of detect invisibility;
unknown duration and permanent effects retain their previous meaning. The
shop controller waits at healer 3054 for a short active spell to expire,
within the ordinary session deadline, then uses its normal verified purchase.
If the timer becomes short while walking to shop 3033, wait there before
consuming a potion; do not spend it on a spell DD4 will refuse to refresh.
DD4 refuses to refresh an already-present spell. Live endpoint detection and
identity checks remain mandatory. Renewed live visibility travel is unproved.

### Ordinary Opponent Joining Combat

`CombatSessionController.ordinary_joiner` owns a finite three-command assessment
for an already-opened XP fight: `look`, `look #<instance>`, then `consider
#<instance>`. Each reply has five seconds; at most eight contexts are assessed
per run, never the same context twice. Look and consider replies must reach
their own complete prompt before the next phase; their text is not parsed as
a new primary-target consider. Require both source loadouts to contain
only known ordinary objects, no poisoned weapon/EGO power, castable item,
script or special. A fresh complete listing must identify precisely two
non-object actors with distinct bound selectors. Source-only object lines may
be ignored only when they do not also match mobile descriptions. Require the
newcomer's globally unique complete source look and a source-consistent live
consider no higher than +1; below-band actors already attacking are not XP
objectives. The original primary retains its own admitted level ceiling.

Use the existing material-encounter combat controller after admission. Preserve
both actors when old GMCP repeats the primary, explicitly marking inferred
levels as look/consider evidence, not live HP. Keep health/lag escape first,
healing and protection resources, the worker's original deadline and every
third-actor/scope check. The legacy 45-second material window does not apply to
this contract. One observed player-level rise can retain the engaged pair;
it grants no new target admission. Preserve a surviving joiner's exact loss
under its canonical source identity and retain the parent trip failure.

Run 24878's pirate 17066 is excluded: its held icicle (17057) casts frost
breath. `fight.c:use_magical_item` permits NPC wand use, and
`magic.c:spell_frost_breath` can shatter containers, drink vessels and potions.
An absent mobile special is therefore not evidence of an ordinary loadout.
The new path is implemented but not live-proven. Tests in
`tests/test_ordinary_joiners.py` are saved for the next permitted batch;
compilation and CLI import checks are not behavioral proof.

### Banked Working Reserve

Before a selected coin-gathering trip, a recovered healer checkpoint with less
than 1,000 copper-equivalent may reuse the existing bank route. Inspect only
the newest bank visit among 256 recent segment rows and its 512-event tail.
Require the same character, successful safe healer return with the working
reserve, and a complete command-local `withdraw 1 platinum` reply containing
the teller's thanks and at least 1,000 copper-equivalent remaining in the bank.
Never fall back past a newer failed, unfinished, or unconfirmed bank visit.
The receipt is provenance, not a retry quota or combat permission. Bank funds
persist across reboots; source refreshes do not erase them. This changes only
`provision-funding` selection, preserving combat, recovery and urgent policies.
Run 24875 confirms the existing route and a 132,614-copper-equivalent balance;
the new selector handoff has not yet been exercised by a live cash shortage.

### Basic Armour Shopping

The city outfit controller owns command-local, 8,000-character shop replies
through a complete prompt, with a five-second deadline. It never substitutes
a keyword purchase for a missing or partial listing. Select the cheapest
uniquely source-matched, class/alignment-legal, releasable offer within the
live level limit; require its exact purchase acknowledgement before wearing.
The final complete `eq all` audit decides which slots remain unfilled.
At the healer, use the shared fixed-budget carrying controller before travel,
reserving one slot per planned item. It may eat one surplus food item and
dispose of at most two surplus food objects while retaining the existing
reserve, with fresh inventory acknowledgements and the original disposal cap.
The version-2 `campaign_city_outfit` receipt retains quotes and outcomes across
funding segments. Only completed healer-return quotes matching level and boot
contribute to the still-empty-slot budget. Fresh prices replace old ones;
boot changes invalidate prices, not hunts. Legacy outfit attempts may make
one pass through this repaired controller. Once funds cover the quoted total,
shopping re-enters normal selection; no combat failure is cleared.
An outfit visit that leaves its planned slots empty is `not_achieved`, even
when execution and safe return succeeded.

Registered singleton policies with explicit source mobile IDs share current-level
exact protected-loss evidence with generic routes. This closes only that mobile,
not independent targets or multi-target siblings. Storn's two registered policies
now carry mobile 19034 explicitly. A new alias must not create a fresh probe for
an already closed encounter.
The optional existing-reserve Sanctuary fallback stops before source search when
a source-verified carried staff has at least two remaining charges. Those charges
cover the permitted initial activation and one repeat during a fight. This is an
anti-maintenance-loop rule, not protection bypass or a reboot retry limit.
Ignore that optional carrier's crowd cooldown when choosing a campaign-wide
wait under the same two-charge condition. Retain the carrier's evidence and
all ordinary hunt, urgent-supply and quest crowd checks.

### Selection Diagnostics

Local preparation expiry has its own timeout type. If it happens during
post-selection validation, checkpoint the latest durable state as ready under
`campaign-post-selection-validation`; no live run was launched. Do not fail
the campaign or report the 300-second live cap plus cleanup as elapsed.
The preparation budget remains 60 seconds, and actual live timeouts retain
their separate failure/recovery handling.
Current-level exact combat losses are not reset-wait candidates. Filter them
before selecting an absence/crowd cooldown; an area reset cannot clear a
combat failure. Preserve the loss ledger and independent absence choices.
Checkpoint 79871's stale Storn wait is excluded by this corrected selector.

`python tools/explain_hunt_selection.py <campaign.yaml> --checkpoint <id>
--full-policy` reads the checkpoint and bounded history using read-only SQLite,
loads the live-deployment source profile, and profiles one bounded selection.
The profile validates checkpoint ownership. It is not a substitute for full
production history repair or fresh live gates. Line rejection tracing is opt-in
and distorts performance; do not infer a production timeout from that mode.
Exact named-source shape checks reject unrelated mobile/room identities before
scanning resets. A selector that reaches its preparation budget returns through
the budget-checkpoint path before any stale crowd/reset wait is considered;
discard only an incomplete frontier diagnosis, never its actual target losses.

### Protection Retry Ownership

`campaign_protection_recovery_retry` uses `status=selected, attempted=false`
while the policy is being chosen and rebound. The exact matching policy may
keep that reservation through repeated selection; another first-loss target
cannot borrow it. At campaign segment creation, set `status=dispatched`, record
`attempt_segment_id`, and checkpoint before opening the socket. Actual route
attempts, including pre-combat failures, remain consumed.
Legacy `attempted=true` markers without a segment ID may be restored only when
two adjacent bounded checkpoints show the marker first appearing in an
unlaunched `awaiting_policy` or selection-budget result. Require unchanged
character, level, boot, source revision, XP/loss ledgers, inventory and resource
receipts, a safe healer checkpoint, and no segment starting after the earlier
checkpoint. Preserve the legacy marker inside the repaired reservation. Run
24869 / segment 24232 reached real dispatch after this repair; checkpoint 79801
links its consumed reservation to the segment, rather than consuming it during
the earlier no-connection selection at checkpoint 79796.

### Combat Healing

Learned combat self-healing permits at most eight attempts per encounter,
retaining the 30% mana reserve (minimum 20 mana), learned-spell checks and
between-round command timing. In field combat, the healing trigger is the
greater of 45% health and the withdrawal floor plus two observed incoming
rounds, capped at 75% health. Only actual incoming damage informs this trigger;
target HP and source damage estimates do not. Field healing never queues a
cast at or below the existing withdrawal floor; retain the command-lag escape
guard and the separate captive-arena behavior.
Run 24869 exposed the earlier three-heal cap with substantial mana still left;
the expanded allowance is saved but not yet live-proven to complete a kill.

### Primary Name Versus Bystanders

DD4 may render a fighting mobile with its short name rather than its idle room
line. A source-bound stop can therefore request `stoic guard` while the combat
line identifies `pirate guard`. The room-bystander controller may exclude that
primary name only with one raw current-room enemy, exact source VNUM, short
name, long description and look description, a complete current-room listing,
and one matching instance selector. Require the bound source reset room and
boot, reject selector conflicts, and record at most eight distinct corrections
per run. Retain genuine bystanders and every other admission/consider/combat
check. The correction never erases a loss or permits another failed attempt.

### Upstream source versus live deployment

`runs/dd4-source` is the current upstream checkout and remains useful for
research, parser tests, and future planning. The live MUD has not deployed the
recent undead and archetype/species changes, and may remain on that deployment
for months. Live campaign loading filters the known unreleased mobile
templates. A narrow compatibility record restores the two Dwarven Home
prototypes 20512 and 20515 from pre-conversion source revision
`6b1ffdab647b3329a056a9d122c2fda59de6b9ec`; it does not add the dwarf template
to the live catalog or bypass fresh identity, route, isolation, consider,
health, or return checks. Other matching area records remain unresolved until
their legacy source is audited or deployment is confirmed. This boundary is
separate from reboot timing and is not a reason to stop selecting other
live-verified targets.

This deployment profile is installed by `CampaignRunner` and by direct
`StarterBotRunner` entry points. Specialized source-world preflights use the
same profile, so a live run cannot accidentally build its route or target
indexes from the newer upstream-only templates. Offline reports remain able
to opt into the full upstream catalog for research. The source-world and
derived mobile-index caches include this deployment mode, so a long-lived
process cannot reuse a research world for a live decision or the reverse.

### Ordered mobile resets

The DD4 reset loader processes `M` records in area-file order and compares the
mobile prototype's current global count with each record's maximum. Once a
singleton prototype has loaded, later same-prototype `M` records are skipped
until the next reset cycle. The source parser therefore keeps every raw reset
for audit, while live candidate ranking uses the effective ordered list. A
later fallback room is not a live target merely because it has its own reset
line. The Pit Official is the concrete example: room 13702 is the first
effective reset; the later room-13703 spectator entry is not a second live
placement.

### Retry rule

Ordinary resume uses the README command without `--retry-stalled`. That flag
requests rotation away from the previous cleared route; use it deliberately,
not on every invocation. A matching visibility-preparation intent now offers
its exact hunt to the normal selector first once the required effects are
active. Match boot, level, source revision, candidate identity and source
mobiles; mark it dispatched only when that hunt opens. Unavailable hints fall
back to ordinary selection and never clear recorded failures.

Consider-history repair selects the newest persisted segment ID after merging
runtime and indexed tails. Repair scan revision 7 revisits the earlier
order-dependent results without changing combat-loss records. Passive singleton
consider allowance includes nominally current-level mobiles whose source load
fuzz can reach the existing +2..+5 tier. The actual live +5 ceiling, target
identity, route, crowd, source hazards and own-health rules remain unchanged.
The final binding step retains a plain Mirror Realm economic-route candidate
only after a fresh current-revision source audit and no prior/current-level
mobile loss or unresolved negative consider. It does not turn arbitrary source
rejections into permission or clear a recorded failure.

Only an unrestricted ordinary hunt search may replace the campaign-wide
empty-frontier diagnosis. Searches limited to special protection, visibility,
ground travel, reserve preservation, or explicit target exclusions cannot prove
that other routes are unavailable. Diagnosis revision 3 invalidates older
shortcuts that may have been produced from these restricted pools without
changing any combat-loss records. Check executable hunts before researching
an optional second protection reserve; both share the preparation deadline.

Registered Catacombs hunts must prepare and verify detect invisibility at the
healer when any selected source mobile is invisible. Nathaniel (9532) is one
such target, and also has `AFF_HIDE`: DD4 `can_see` requires detect hidden
separately. Without it, choose visible siblings or mark the hidden route
unavailable rather than dispatching another blind visit. An empty room without
both capabilities does not prove Nathaniel's absence.
The resource catalog and consumable acquisition path recognize `detect-hidden`
(`detect hidden` is also accepted). Its maintenance kills are not progression
objectives. The first Ambush acquisition stopped on Essabella (4521, level 12,
`spec_guard`) beside carrier 4520 in room 4528. The corrected contract permits
one exact singleton, nonaggressive guard whose maximum source level is at
least ten below the player, with no scripts, weapons, spell items, damage
modifier, or offensive equipment bonuses. Armor and detrimental inert
restraints are audited in `mobile_loadouts.py`. This does not claim the guard
cannot assist: `spec_guard` can intervene and use headbutt, smash, or kick.
Require the explicit stop allowlist and a fresh exact-instance low-band
consider before the carrier fight. Other crowds and live withdrawal rules
remain. A pre-combat stop solely on that corrected source shape may re-enter
the live gates without clearing an actual combat loss.

Run 24844 considered both exact mobiles, killed the carrier, and acquired
potion 4558 without HP or XP loss; it does not prove handling a sustained
two-enemy fight. Run 24845 consumed the receipted potion at the healer and
verified detect hidden in GMCP. Healer-side activation uses a source-bound,
live-carried receipt and the existing acknowledgement/consumption controller.
A carried receipt alone is not proof of an active detection effect.
Registered and exact-bound generic hunts now share `_prepare_hunt_visibility`,
including every source mobile in a selected circuit. The final dispatch
boundary repeats the check after policy rebinding or late route rotation.
Acquisition and activation handoffs retain the intended policy and mobile IDs
as provenance, not combat permission. The travel controller also checks
current effects before an unseen source-hidden/invisible target can become an
absence result; expiry causes a preparation return, not a false absence or
combat loss. An already visible selector still goes through normal identity
and consider checks. Run 24847's earlier empty Storn stop (19034, `AFF_HIDE`)
remains visibility-unverified evidence, not proof of absence. Nathaniel's run 24846
did reach a visible, positively considered target, but withdrew with a net
439 XP loss; preserve that actual combat loss independently of vision fixes.
Withdrawal capture must survive the outgoing flee/recall command while combat
is still active. Only the later XP-loss observation consumes that exact-target
receipt; a continuing combat action may clear a stale pending withdrawal.
Startup registered-loss repair owns historical identity recovery, not the
selector's temporary state. Inspect at most four linked current-level losses,
each with at most four explicit penalties and 128 preceding ordered events.
An exact source presence receipt supplies a candidate only; matching live
enemy VNUM, withdrawal, room and XP penalty must prove the negative identity.
Checkpoint **79707** verified persistence of Nathaniel's run-24846 loss as
`source-ranked-hunt-vamp-catacombs-9532-9574-45`, net **-439 XP**. Neither
compact summaries nor an empty legacy loss list clear that failed target.
The existing see-invisible purchase path owns stock, price, and effect checks;
a recorded purchase failure blocks another blind visit, not the target's combat
identity or loss ledger.
For a registered multi-target policy, that purchase failure excludes only its
source-invisible siblings; already eligible visible siblings retain the normal
route and combat checks. An exact-bound generic circuit is not silently
rebound or partially rewritten to evade its detection prerequisite.
Resolve an unavailable invisibility prerequisite before spending another
segment acquiring or activating detect hidden for that same target. A
detect-hidden resource cannot repair missing detect invisibility.

A source-viable target is never closed because a locator retry was dispatched,
a retry marker was recorded as consumed, or the MUD rebooted. A loss-free
absence is locator evidence only. A short scheduler cooldown may prevent an
identical command from being issued immediately, but it is not a per-reboot
quota and does not require a reset before the target can be revisited. Later
bounded visits may re-admit the target whenever fresh source, route, identity,
live `consider`, health, crowd, and loss checks pass. Only fresh terminal
evidence such as a loss, crowd, route hazard, identity mismatch, or negative
`consider` closes that exact target.

Startup must also ignore a bare absence/crowd cooldown when the result that
created it belongs to an older DD4 boot. A reboot is a fresh locator
observation, not permission to keep a viable target closed. This does not
erase or reopen a durable combat-loss record, source hazard, identity failure,
or negative live `consider` for the exact target.

The generic source-ranked frontier-retry receipt is diagnostic provenance, not
consumption state. It cannot close a viable target for the current reboot or
turn a later bounded retry into a one-shot entitlement; the ordinary fresh
source, route, identity, `consider`, crowd, health, and loss gates remain the
actual admission rules.
When multiple loss-free current-band absence candidates are eligible, the
selector prefers one without a same-context dispatch receipt before repeating
an already checked circuit. This only improves rotation; after the alternatives
are checked, every still-viable target remains reusable.

When the ordinary source frontier is otherwise unavailable, a normal campaign
invocation may reopen one loss-free current-band absence for a bounded live
recheck. This is the same bounded rotation previously exposed by
`--retry-stalled`; it is not a reboot wait or retry quota, and exact current-
level, prior-level, same-mobile loss, hazard, and live gates remain in force.

A source-ranked route hazard closes only the exact route that produced it; it
does not make the whole current-band frontier wait for a reboot. The campaign
records a `frontier_recheck` checkpoint and can rank independent routes again
on the next bounded invocation. Explicit crowd, absence, and Sanctuary reset
contracts retain their separate wait behavior.

### Armed transit noise

A source-proven armed route mobile may be treated as transit noise when its
fuzzed maximum level is at least four levels below the pilot, its total reset
population is at most two, and every reset has one known weapon plus armor
only, with no scripts or specials. This is route permission only. It does not
authorize combat with the mobile or the selected endpoint; live identity,
consider, crowd, Sanctuary, health-floor, and return checks remain mandatory.

### Vampire Catacombs, levels 41-45

The current-level fallback uses a distinct `vampire-catacombs-hunt-41-44`
policy so it does not inherit the 38-40 campaign result. Once generic selection
has no executable route (or ranks only a weak solo probe), it can use the
source-verified recall route to the room-9571 bouncer; characters above level
14 are transferred into room 9500. The exact candidate set is Grok (9510), the
wandering art critic (9545), Mavralyn (9523), Augus (9541), and Grieb (9542).
The last three require the verified spiked key, whether carried or confirmed in
the current-boot room-3007 cache. Grok still requires a verified Sanctuary
reserve. Every reset is re-audited, and fresh live identity, isolation,
consider, combat, and return checks remain mandatory. Absence or reboot timing
does not create a permanent target ban.

The active Dorrik checkpoint is **79749** (campaign **39**, latest gameplay
run **24861**); Dorrik is level **45** with **2,106,667 XP**, 18 quest
points, and **6,333 XP** remaining to level 46, safely recovered at the
Midgaard healer in room **3054**. Older
campaign **7** history is blocked and must not roll the character back. Resume
is profile-owned: the runner chooses the newest resumable history across
generated and legacy config paths and reattaches it to the requested campaign
file. The exact Ra loss remains closed; preserve loss records and do not
reopen lost targets merely because recovery succeeded. The current source
mirror is **66f1f42675c0da46966ef3f15d96b06e191a0660**;
live deployment remains a separate, older profile. Run 24857 returned after
detect hidden expired before the source carrier could be located. This is
capability-preparation evidence, not an absence or a progression kill.
Run 24861 reached the exact Storn fight with verified Sanctuary, then withdrew
without a kill for **242 net XP lost**. Its live withdrawal receipt retained
mobile **19034**, reset/live room **19114**, level **45**, partial XP and the
protected-loss flag. Keep that current-level target closed; do not treat
successful recovery or the earlier consider correction as retry permission.

Runs **24678** and **24681** ended with exact Hephaestus-carrier XP losses;
keep that carrier closed. The Sanctuary-loss parser now recognizes the
`-sanctuary-maintenance` policy suffix and records losses for fixed carriers,
not only Moria executions. This change has static validation but still needs
the next allowed regression batch. Runs **24684-24685** safely checked absent
Alchemist and blue-tongued-lizard resets. Run **24686** defeated the source-
verified Sewer red dragon, acquired object **7303** (the held Red DragonOrb
Sanctuary staff), and recorded **10 charges**; Dorrik returned to the healer
with **290 XP** gained. Run **24687** safely checked the Mirror Realm Storn
route and found him absent. Run **24688** safely checked the Freeport route to
Admiral Blacksail and found the target absent; no fight started and no XP was
gained. Run **24689** selected the Kaladim cave beast (9936, room 9951) after
an experimental aggressive-fuzz admission. On arrival, DD4 showed it fighting
Dorrik and the policy recorded a below-band sighting before any `consider`;
Dorrik fled without attacking, losing **1,405 XP**, then returned to the healer
at full health and logged out. Checkpoint **78794** preserves that exact
current-level loss, which closes this target. The experiment showed a plain
aggressive sentinel cannot be opened to level-fuzz probing unless the route
keeps it invisible through endpoint inspection, so the admission was reverted
and the focused test now expects the source gate to reject this shape. That
updated assertion is not yet pytest-verified. The held Sanctuary staff still
has **10 charges**; one separate source-eligible Dwarven Home recheck may repair
its prior unprotected plain-target loss, subject to fresh live gates. Do not
reopen the Kaladim loss or attack without a live useful `consider` result.

As of November 14, run **24812** reached the Dwarven Home gambler and ended in
a safe withdrawal with **489 net XP lost**; preserve that exact target loss.
Runs **24813** and **24819** attempted the Catacombs fallback but started no
combat and gained no XP. Run **24813**'s transcript shows the light-blue
potion's GMCP flight duration expiring before an eastward interior Catacombs
exit; do not repeat that same setup as if it were a productive hunt. Run
**24819** is a separate no-progress attempt; retain its own evidence. Intervening provision,
loot-sale, and gnome coin-stash segments completed safely. Run **24818** made a
bounded Storn probe without progress. Checkpoint **79516** is current and the
ordinary source-ranked frontier still reports no executable target; continue
finding an independent live-considered current-band route rather than treating
these empty or setup visits as progression.

At level 45, Grok's ordinary XP route closes because his source range is now
below the useful band. The source-gear controller may still select the exact
`vampire-catacombs-grok-belt` maintenance plan when Dorrik lacks a better waist
item: it requires the source-verified singleton loadout, a current Sanctuary
reserve, 90-percent entry health, the verified bouncer route, live identity and
consider checks, and a retained belt receipt. The kill is maintenance evidence,
not progression XP, and an exact current/previous-level loss still closes the
plan.

Run **24202** reached Grok and confirmed the passive, armed `spec_warrior`
carrier and the belt room, but the protected fight ended in a 50-XP loss and
death before the belt was acquired. Dorrik recovered the corpse and returned
to the healer; the exact Grok maintenance receipt is now closed and must not be
retried. The live transcript also exposed a transport race: after a combat
recall command left Dorrik in the same room, the controller waited for delayed
failure text while automatic rounds continued. The starter now switches to its
bounded flee path on that unchanged-room combat prompt, while retaining the
old wait behavior for noncombat delayed recalls.

Runs **24214** and **24216** exercised the repaired ordinary frontier path:
Admiral Blacksail and the Pit Official were each given a bounded live locate,
both were safely absent, and Dorrik returned full to the healer with no XP or
additional loss. Runs **24223-24225** then repaired and verified the healer
stance handoff, including re-wielding the primary weapon after recovery. Run
**24226**, **24234**, and **24239** safely revisited or checked current-band
routes with no XP loss. The normal
campaign command performs one loss-free same-boot absence rotation without
`--retry-stalled`; it reuses the audited source catalogue so the retry cannot
consume the preparation budget on a second full ranking pass.

The exact White Lotus Chief route (mobile **10734**, room **10836**) is now
source-audited through the Miden'nir `where` checks for the two deep below-band
unarmed wanderers. The old preflight result and the adjacent-scan result from
run **24232** are recognized as stale, retryable evidence for this exact
policy. The current selector may revisit it; live mage identity, `consider`,
Sanctuary, blindness recovery, crowd, health-floor, and healer-return gates
remain unchanged.

The Nov 4 bounded invocation selected the source-audited Mirror Realm
proprietor route and safely achieved **7,993 XP**, returning to the healer with
**2 Sanctuary charges** remaining. Fresh live identity, isolation, relative
level, consider, Dorrik's 20% health floor, provisions, and return checks still
decide every fight; target HP remains observation only. The next invocation
should use the normal campaign command and verify the newest profile-owned
checkpoint rather than naming an older campaign ID.

Run **22652** also reached live play: its 140-command transcript shows Dorrik
fought a level-40 orca before reaching the selected Pirate Isles guard, dealt
1,004 XP worth of damage, and paid a 1,330 XP recall penalty (net **-326 XP**).
The earlier recovery annotation claiming no live commands was wrong; Dorrik
escaped and run **22653** returned him safely. Do not repeat that 115-command
guard route without a distinct source-audited approach. The incidental orca
remains a separate target subject to its own live consider and combat gates.

Run **22657** reached the Kerofk Recruiting Office and live-considered the
Sergeant. “Laughs at you mercilessly” means the target is 6-9 levels higher
under `act_info.c`; the accompanying “built like a tank” line compares hit
points and is observation-only. Reject this target for its level, not its HP.

The healer-side rearm controller now accepts a verified primary-plus-pounding
weapon pair at room 3054 even when a saved shop route begins elsewhere. This
repairs the stale-origin failure recorded in run **22655**; its focused test
was added and the touched modules compile. The November 10 full regression
allowance is spent; the focused runner/recovery sweep passed 19 tests, with 9
additional route-hazard campaign checks now passing.
The upstream checkout has since added area conversions and mobile-archetype
revisions across Fleshmonger, Kaladim, Dragon Cult, Shaolin, Juargan, Freeport,
Smugglers Ship, Fortress, Foundry, Dangerous Neighborhood, Mega-City One, and
Abandoned Cathedral. These changes are not deployed on the live MUD; live
campaign loading keeps the known unreleased or revised templates unresolved
until deployment is confirmed.

Route admission and emergency return still require fresh source, identity,
consider, and own-health checks. Runtime Sanctuary and consider-repair history
uses bounded phase tails (256 rows normally, up to 1,024 for the active
consider repair), while full current-boot combat-loss history remains intact.
Preparation reports separate Sanctuary, consider, and combat-loss
reconciliation stages. The November 10 full-suite allowance is spent; rely on
focused checks, compile, and whitespace validation for further edits today.

### Offline service boundary

When `dragons-domain.org:8888` refuses the bounded connection, leave the
campaign checkpointed and do not start a worker or spin on reconnects. Offline
work may still inspect the read-only database, refresh source-derived reports
with `--live-deployment`, compile touched Python modules, and repair code or
documentation. Resume the single Dorrik campaign only after the service is
available; the next invocation must use the saved healer checkpoint and the
existing provisioning gate rather than inventing a new character or route.
Out-of-band kills remain allowed when acquiring or restoring Sanctuary, but
their XP is recorded as maintenance rather than progression. Segments
**2347-2348** safely checked an absent Lotus Temple target and a present
Freeport target that failed live `consider`; neither changed XP.
Run **20563** killed the Kerofk Receptionist for **2,105 XP** without a safety
loss. Runs **20569-20577** mixed clean Clive, Receptionist, Astral Guardian,
and Mr. Teece kills with correctly recorded health-floor losses. Runs
**20584-20599** continued that pattern, including the bounded-command-budget
Receptionist segment, recovery, provisioning, Hawklord and Teece progress,
and exact-target loss closures. The plain-instrument loadout fix now prevents
the banjo from reopening that gear loop. A viable unresolved Sanctuary receipt
remains retryable; only a terminal outcome closes its exact carrier.
Run **20569** recorded Athena's safe **1,125 XP** health-floor loss; run
**20570** then killed Clive the Weapons Master for **2,957 XP** safely, leaving
**4 Sanctuary charges**.
Run **20572** then killed the Kerofk Receptionist for **1,804 XP** safely,
leaving **3 Sanctuary charges**.
Runs **20573**, **20575**, and **20577** then added **3,678**, **2,600**, and
**4,017 XP** without safety losses, leaving **1 Sanctuary charge**.
An observed viable Sanctuary research receipt without a completed kill,
acquired object, absence, loss, hazard, or other terminal outcome is unresolved
and must not exclude that exact carrier from a later bounded maintenance retry.
Run **19999** acquired the Staff of the Bard as an out-of-band Sanctuary
maintenance objective; later protected hunts consumed or lost that earlier
reserve. Run **20561** acquired a fresh 10-charge red dragonorb. Runs
**20006-20007** safely tested an alternate reserve route
and a world-time probe without claiming progression XP. Runs **20008-20011**
then checked fresh source-ranked locations; each was safely below-band or
absent, so the retry-stalled rotation also checkpointed without opening
combat. Out-of-band kills remain allowed when acquiring or restoring
Sanctuary, but their XP is recorded as maintenance rather than progression.
When a safe healer checkpoint has a live reserve but no executable current-band
route remains, the controller may top up that reserve from a fresh out-of-band
carrier after gear and quest gates; this is still maintenance, never XP-band
permission. A carrier may be below or above the ordinary XP band: the exact
source reset and live `consider` still decide whether it is fightable, while a
confirmed kill is recorded as maintenance rather than progression XP. After a
bounded area-reset boundary, recheck each exact absent carrier once. One miss
does not make unrelated carriers wait for a reboot.
Windows hidden workers must report the actual Python PID through
`tools/launch_hidden_worker.py`. If a live attempt produces no durable
checkpoint by the five-minute worker boundary, stop that worker tree, preserve
the last healer checkpoint, record the interruption, and continue local work;
never leave a detached command wrapper running or start a second gameplay
connection.
After login, a dispatched command must receive a prompt or authoritative room
acknowledgement within 12 seconds. The longer general inactivity timeout still
applies while deliberately sleeping or otherwise waiting without a command in
flight. A missing command acknowledgement gets one bounded `look` probe and a
reconnect, rather than consuming the rest of the live segment; record the
command, probe, reconnect, and resulting checkpoint as transport evidence.
Run **19955** closed a Smugglers Ship transit interception by armed Crewman
mobile **17517** after a safe **1,060 XP** loss; the source audit now covers its
paired **17503/17517** family. Run **19956** reached One-eye (mobile **17500**)
and withdrew at **109/943 HP** for another **1,060 XP** loss because the
verified Sanctuary staff was activated too late. Run **19957** confirmed the
hold step but exposed a missing `brandish` follow-up; run **19958** reached the
White Lotus guard safely and stopped before combat after a campaign handoff
dropped the staff receipt. The handoff now recognizes structured GMCP equipment
and preserves the 10-charge reserve. Ordinary armed hunts enable it at the
opener while retaining live identity, consider, route, crowd, and health gates.
Run **19176** deliberately tested the newly admitted, source-fixed Hercules
route: live identity and `consider` passed, but Hercules' level-40 attacks
forced a correct 20-percent health-floor withdrawal and a net **-115 XP**.
That exact target is closed for this boot. The next source-ranked option is the
singleton, unarmed Kaladim mirror (mobile **9934**, room **9943**), whose long
route is bounded by source-identified lower-level transit hazards. Policy
revision **360** treats target hitpoint affects as evidence only on bounded
economic routes; it does not waive weapons, specials, crowd, route, consider,
or Dorrik's own health and recovery gates.

The latest durable checkpoint is **58486** (campaign **35**, latest live run
**19116**). Dorrik is level **39** with **1,295,991 XP** and is back at the
Midgaard healer after corpse recovery. Runs **19108-19114** claimed no XP;
runs **19115-19116** safely added 80 and 90 XP through Moria recovery.
Run **19112** safely reached the Ota'ar approach but an adjacent source hazard
stopped it before the arena; the corrected campaign record is
`execution=success`, `objective=not_achieved`, `safety=safe`. Run **19087** used
the one-shot Sanctuary retry to kill Orion (mobile **9311**, room **9328**) for
**3,103 XP**; run **19089** later re-tested that productive route and withdrew
at the 20-percent health floor after **154 incoming damage**, losing a net
**441 XP**. Preserve that exact same-boot loss and do not replay Orion. The
current worker must find a different audited route or wait for fresh evidence.
Level-40-plus psionics remain excluded unless disintegration protection is
freshly verified from both source and live evidence.
Run **19090** then completed the bounded reset wait and world-time probe safely;
the DD4 boot was unchanged and no XP was claimed. The maintenance-only
checkpoints **58346** and **58380** opened no gameplay connection and claimed no
XP; both reports record `execution=success`, `objective=not_achieved`, and
`safety=safe`. The current frontier remains closed by same-reboot evidence, not
by permission to
engage a level-40+ psionic. Run **19107** exposed an unsafe failure path:
the previous water-shop funding failure left Dorrik in room **27340**, where a
later reconnect found him at negative HP and DD4 killed him before the death
transition was observed. The bot recovered the corpse and returned safely, but
the segment is `safety=unsafe` and claimed no XP. The controller now funds the
live water quote with at most four distinct redundant armour sales, returns to
the source-verified no-mob room **27347** before surfacing an unrecoverable
failure, and refuses to save or quit when a reconnect reports nonpositive HP.
The linked run report for **19112** may still show a successful flight objective;
that is preparation evidence only. Campaign source-hunt segments now require
confirmed objective-kill evidence, so preparation cannot be reported as hunt
progress.

Run **19058** safely persisted the startup repair for the consumed two-potion
Moria refill marker. The MUD had not rebooted, so the marker remains closed as
`no_object` and no XP was claimed.

Run **19060** is a closed live-loss record, not objective success. The Lotus
Temple duplicate-population retry reached room **10820**, where four shrine
attendants were present; the Golden Buddha joined the fight through DD4's
generic same-room combat-assist loop despite its otherwise beneficial
`spec_cast_adept`. Dorrik withdrew safely and lost a net **832 XP**. Keep that
room closed for this boot and do not treat a noncombat special as permission
to ignore room companions. Checkpoints **58113** and **58117** then found no
executable ordinary current-band route without opening another gameplay
connection.

For ordinary source-ranked XP hunts, consider every source-supported target
through the active character's `+5` level band. The live `consider` response,
exact source identity, route, crowd state, and source hazards decide admission.
Target hitpoints, weapon output, Sanctuary, damage-window estimates, and
equipment projections are observation/report evidence only; they must not make
a plain target ineligible or trigger an automatic flee. Preserve source
specials and aggression hazards, identity and isolation checks, provisioning,
movement and recovery checks, and the character's own health withdrawal floor.
Historical rejection records remain evidence for their exact target and boot;
they are not permission to reject an otherwise valid current target merely
because an old predicted output estimate was unfavorable.

Before committing to a field fight, a complete current-room TARGETMODE listing
is authoritative crowd evidence. Merge its targeted mobile descriptions with
cached text and GMCP counts by taking the maximum count per source identity;
later prompt packets must not erase a visible bystander from the pre-combat
audit. This strengthens observation only and does not relax source identity,
consider, isolation, or combat-loss gates.

An exact current-level combat XP loss closes that mobile VNUM across all of
its reset rooms; another reset room is not a way to retry the same target.
Keep unrelated mobile siblings eligible, and keep route-only losses scoped to
their recorded route hazard. The original exact policy can use only its
explicit, narrowly approved revalidation. After ordinary current-band
selection is exhausted, one
`campaign_source_ranked_prior_level_loss_revalidation` may reopen an exact
same-boot loss from the immediately previous level when the new level has no
loss for that reset and the source-safe/current-band gates pass. Consume the
receipt before dispatch, retain the original loss, and close it on any failed
or mismatched attempt; it is not a general cooldown reset.

Sanctuary acquisition is a maintenance objective rather than an XP-band hunt.
When the fixed recovery sources are exhausted, the source-ranked maintenance
rotation may select an exact carrier outside the ordinary useful-XP band. The
same live `consider`, source identity, isolation, route, health-floor and
required-loot checks still apply; source HP and damage estimates are evidence,
not a pre-live admission veto. Record the kill as maintenance and exclude its
XP from progression metrics. A same-boot absence closes only that carrier, so
unrelated Sanctuary sources remain eligible without waiting for a reboot.
If a safe healer checkpoint already has a Sanctuary reserve but the current-
band selector is exhausted, the same rotation may make one fresh top-up
attempt after source gear repair and quest gates have been considered. It must
not pre-empt an executable current-band target or an active quest.
During an admitted fight, one post-expiry refresh may come from the same
source-verified charged Sanctuary staff after the live effect was observed.
Keep exact target identity, health, and remaining-charge checks; pouch potions
remain single-use in that fight.

`spec_cast_psionicist` is a hard protection gate. DD4's source spell table
opens energy drain at mobile level 14 and disintegrate at level 35. Do not
engage a candidate in either band without a fresh source- and live-verified
protection receipt. The concrete player bypass in `spell_disintegrate` is
Phoenix form (or a player-killer room); otherwise a failed save can destroy
carried objects and the follow-up check can kill the player. Sanctuary, Globe,
energy containment, Illithid psychic resistance, and the Crysomer item's prose
description do not prove immunity. This keeps level-40+ psionics out of the
live target set until a real protection path is evidenced.

The Sanctuary recovery selector has one further exact fallback after the
primary, alternate, Alchemist and Athena routes close: Hephaestus, mobile
**908**, in Olympus room **937**, with nectar object **926**. Source review
proves a singleton level-38 sentinel with only `spec_breath_lightning` and a
non-weapon reset. The special exception is carried only on that exact stop;
fresh live identity, isolation, `consider`, player-health, provisioning and
return checks still apply. It is a required-loot recovery route, not XP credit,
and it does not alter the psionic/disintegrate boundary above.

The level-39 source-ranked XP frontier also has one deliberately risky,
identity-bound exception: the Ancient Gold Dragon, mobile **631**, in Ofcol
room **693**. The current source reset proves one level-37, non-aggressive
sentinel with `spec_breath_any`, the Golden Claw and Dragon Orb, plus two level-
21 attendants. The attendants' `spec_cast_mage` only selects victims already
fighting the attendant; they are not aggressive or guard-assist mobiles, so
this exact chamber shape does not create an automatic crowd fight. The
exception accepts the dragon's random acid, fire, frost, gas, lightning and
steam breath as real combat risk, and requires Sanctuary, fresh live identity,
isolation, `consider`, route/recovery checks and the normal 20-percent health
floor. It does not generalize to other breathers, endpoint casters or
psionics, and it does not waive live target or abort checks.

Source `special.c` confirms that `spec_breath_any` selects among acid, fire,
frost, gas, lightning and steam. Live segment **22274** showed why Sanctuary
is not enough by itself: Ra (mobile **919**, room **931**) used acid and gas
after the Sanctuary effect expired; recall failed while the fight was active,
and Dorrik died before the escape completed. The exact current-level loss stays
closed. The field controller now prefers its bounded flee path after a
protected breath fight loses Sanctuary and does not issue another recall while
DD4 still reports combat. This is an escape correction, not permission to
reopen Ra or generalize the breath exception.

Policy revision **359** also opens a source-audited Mirror Realm transit
exception for the level-39 frontier. The route from Midgaard recall crosses
the exact wandering gardener (mobile **19036**), whose `spec_thief` code only
handles coin theft; its wielded clippers do not turn that special into a
combat hazard. The same route's low-level fido and known Midgaard guard
resets remain recorded hazards, and the live runner still checks each room.
The exception requires the exact gardener reset, fido population, route and
target reset shape, known purse no larger than **1,250 copper-equivalent**,
fresh identity and isolation, live `consider`, and the ordinary 20-percent
health floor. Exact source-ranked singleton fights use that own-health floor
without stacking observed incoming damage or target-output budgets; those
measurements remain evidence for reports. It admits plain current-band targets
and can admit the Grey Fox (mobile **19047**, room **19146**) as one aggressive,
unarmed singleton with the source-safe `spec_fido` procedure only when its
source lower-level bound remains above the useful-XP floor. At Dorrik's level
39 that bound is not sufficient, so the live runner must close the Grey Fox
after a level-34 observation rather than paying another pre-combat flee.
For the exact plain armed Mirror Realm stops, the runner now proactively
uses a verified Sanctuary reserve when one is already carried; an absent
reserve does not close the plain target or override live `consider`.
Revision **359** extends the same bounded no-Sanctuary fallback to any source-
fixed singleton with exactly one ordinary weapon, no target special or script,
one room reset, and no hard route hazard. This is a live probe, not a damage
prediction: exact identity, current `consider`, crowd state, the character's
own health floor, and the return route remain mandatory. Endpoint casters,
psionics, extra weapons, and stale failed targets remain excluded.
The source-ranker has one additional route-only allowance for plain Mirror Realm
endpoints: fixed `spec_thief` mobiles **19044, 19045, 19046, 19052, and 19053**
may carry audited ordinary non-spell reset gear because `special.c` shows that
the procedure transfers coins and does not attack or cast. The campaign must
still supply the exact route and purse receipt, retain the original economic
rejection, and recheck source identity, isolation, `consider`, health, and
return gates. This does not apply to a special endpoint such as the Grey Mare
and never authorizes combat with any thief.
The source audit also treats a passive singleton reset in each of at most two
distinct rooms as the same bounded target shape when every reset has the same
ordinary loadout. This admits the Black Lord and the colour lords without
requiring Sanctuary; their one ordinary weapon remains a real live-combat
risk, so the character's own 20-percent floor, current `consider`, exact
identity, isolation, route, and return checks still decide the fight. A route
with an additional combat-joining special, such as the alternate Black Lord
approach through the level-40 waiter, remains closed. It does not permit
fighting the gardener,
fido, guards, or any other special target, and does not weaken the psionic or
energy-drain boundary. Once the checkpoint has a verified Sanctuary reserve,
the older protection marker no longer forces another refill segment; ordinary
current-band selection resumes and the reserve is available for the audited
combat routes that need it. If the exact recovery policy is exhausted or on
cooldown while no reserve exists, reserve-preserving selection is likewise
released so an already-audited ordinary target can compete; this is not a
blanket protection bypass.

The first bounded Hephaestus selection exposed a dispatch mismatch: run
**19055** executed the generic Moria route and reported object **4050** under
the Hephaestus policy. Preserve that run as Moria evidence, but do not treat it
as a Hephaestus acquisition. Startup repair checkpoint **58064** invalidates
the mismatched receipt and records the expected nectar **926**; the executor
now fails closed unless mobile **908**, room **937**, its lightning special, and
object **926** are all bound together. Checkpoint **58117** confirms startup
history reconstruction no longer recreates the invalidated **4050** result.
This repair does not relax the hard
`spec_cast_psionicist` protection gate.

Runs **19056** and **19057** are valid Alchemist-carrier results. Their exact
live identity and consider checks passed, but the player withdrew at the
20-percent health floor, losing 1,000 XP on each run after 187 and 156
observed damage respectively. Both runs finished safely at healer room
**3054** and remain closed for this boot; run **19057** exposed that
`--retry-stalled` could bypass the old policy result. The selector now closes
the exact source mobile/room/level/boot loss across generic and named
Sanctuary fallback paths. Do not treat a safe return as objective success or
retry that carrier without fresh boot/source evidence.

An already-productive, current-boot, loss-free plain route may receive one
`campaign_source_ranked_productive_transit_revalidation` when its only
remembered crossing is a source-bounded below-band aggressor. The marker
requires a safe healer checkpoint, unchanged source/level/boot, a useful
completed kill, an exact singleton target, and a fresh live route, identity,
consider, health, and recovery audit. Consume it before dispatch. This repairs
one repeat route only; it does not clear a target failure or waive another
route hazard.

When Sanctuary recovery is terminal and no ordinary current-band route remains,
the separate `campaign_source_ranked_fresh_transit_probe` may admit one fresh
unarmed target at one exact fixed-sentinel reset whose source cap is at most four
and whose only remembered route interruption is a source-bounded borderline
aggressor. The marker is bound to the current boot, level, source revision,
target identity, room and complete route; it is consumed before dispatch and
closes as `no_kill` unless that exact segment records an objective kill for the
marked source mobile. An incidental transit kill does not count. Live identity,
consider, crowd, health-floor, output, return and recovery checks remain
authoritative, and the probe never reopens an old target loss.

## Password-Only Transit

The source audit now distinguishes an automatic transfer from an inert fixed
password teleporter. A separate proof requires a passive sentinel with one
singleton reset, no equipment/inventory or special, and one to four explicit
phrase-only speech programs. Each may contain only `mptransfer $n ROOM group`
to a source-known room. The original `player_relocation_programs` evidence is
preserved. Walking past is permitted; speaking the password and routing through
its transfer are not approved by this proof. Mixed/automatic/unknown scripts
retain their normal rejection. No combat admission is granted for the actor.

At checkpoint **79871**, this removed the false relocation rejection from the
ordinary walking route to sand worm **39004**. Full-policy selection chose that
hunt without a target-HP gate. Run **24880** subsequently walked past the actor,
passed live consider, killed sand worm **39004** for **4,862 XP**, and returned
fully recovered to the healer. Checkpoint **79876** is level 45 with 2,111,948 XP,
1,052 short of 46; execution success, objective achieved, safety safe.
Regression cases in `test_password_transit.py` remain saved but unrun under
November 14's spent allowance. This live proof does not replace that batch.

Run **24884** subsequently failed against dust dweller **39008**: no kill,
1,405 flee penalty minus 896 partial XP, **509 net XP lost**. Dorrik escaped,
fully recovered at the healer, and checkpoint **79899** retained level 45 and
2,111,559 XP (1,441 short of 46). Keep this exact current-level loss closed.
Its ordered replies exposed a timing error: self-heals ignored the ordinary
command window and cooldown, queuing casts ahead of escape. Self-heals now use
the same reply/lag window, including failed recitation and their exact healing
reply; background rounds or aura wear-off cannot release it. The health-floor
escape stays earlier. Compilation passes; new timing regression cases remain
unrun under the daily allowance.

Run **24885** killed sewer dragon **7040** and acquired the Red DragonOrb;
classify its 280 XP as incidental maintenance. Run **24886** then killed a fresh
sand worm **39004** (4,150 XP) and tiny mouse **39011** (5,423 XP), with no flee
or XP loss. The worm raised Dorrik to 46, confirmed independently by text and
`Char.Worth`; the circuit continued to the mouse. Eight bounded self-heals were
issued without the old prompt-driven queue burst. The completed summary records
9,573 net XP over 293 seconds including travel and healer recovery (about
1,960 XP/min), objective achieved and safety safe. Checkpoint **79910** preserves
level 46, 2,121,412 XP, and full recovery/logout in healer room 3054. This is live
timing and multi-kill evidence, not a substitute for the unrun regression cases.

## Combat Cadence And Trainer Returns

After run **24886**, reply acknowledgement and lag were respected, but a quiet
interval could leave the decision gate closed until another enemy round.
`CombatCommandWindow` now offers one timed wake-up after an acknowledged
command's existing wait. Its scope binds room, exact selector/prototype, level,
boot and hunt stop. Changed/missing scope cancels it, and pending/suspended
commands cannot wake it. The runner still requires the actual transport prompt
before calling the policy, which rechecks the ordinary combat gates. The
`timer_wakeups` counter records gate reopenings, not hits or damage. Source skill
waits and the own-health floor are unchanged. Run **24894** proved 17
acknowledged commands, 11 timed wake-ups and no timeout. Its flamestrike/kick
rotation alternated near 3.5/2.5-second gaps and killed dwarf **20514** for
3,771 XP, returning recovered to the healer. Checkpoint **79938** records level
46 and 2,124,177 XP. The block since **79910** gained 2,765 net XP after including
the 120-XP supply kill and **24893**'s 1,126-XP Storn loss; keep that loss closed.

Run **24889** exposed a different failure: a trainer progress cursor survived
the healer return, producing alternating sleep/stand commands until the fixed
500-command cap stopped the run. That result remains failed, with no XP loss.
The healer now terminates the optional visit as deferred, preserving practice
balances and explicitly recording any unconfirmed choice. It does not credit a
lesson or complete a required skill; mandatory training fails safely instead.
The actual command-in-flight timeout remains transport-owned. Run **24890**
passed that old trap, reached the detection-supply objective and completed its
healer recovery at checkpoint **79925**. These focused cases compile but are
saved unrun for the next permitted regression batch.

Run **24893** also exposed a legacy-route combat omission: a stop without
`source_combat_action` used repeatable kicks but starved the Knight's known
flamestrike. An already-admitted fight may now choose a source-registered,
live-known class damage spell when that field is absent, alternating it through
the existing repeatable-action loop. Preserve explicit source plans, exact
targeting, proficiency, unavailable-spell and mana-reserve checks; no fallback
opens combat or changes target admission. This correction is saved and compiles
but has not yet been live-proven, and it does not reopen Storn's level-46 loss.

## November 14 Continuation

Run **24895** escaped Ben **30210**, losing 1,480 XP but receiving 1,344 partial
XP: net **-136**. Keep this exact level-46 loss. Run **24896** then killed
**20513** for 3,705 XP and **20514** for 3,356 XP: **7,061 net XP**, safe healer
return. Run **24897** made no kill. Checkpoint **79950** is level 46 with
2,131,102 XP, recovered and logged out at the healer; block net since **79938**
is **+6,925 XP**.

The first kill in **24896** is incorrectly tagged below-band in old evidence.
The bounded pre-kill GMCP tail proves mobile **20513**, level **44**, matching
the source descriptions; its instance-specific consider was an easy kill at
pilot level 46. A name lookup for "the player" overrode those stronger facts.
Runtime classification now returns from live level first, then exact-VNUM
source range, before using any name fallback. The low-level namesake cannot
override a useful-band enemy. Existing records, source losses and negative
consider evidence are not deleted or automatically repaired. Cases compile
but remain unrun under the spent daily allowance; a new live classification
receipt is still required.

The Astral hammer **1900** is not a clear upgrade over demon blade **16086**:
both add 10 damroll, but the hammer trades +10 hitroll for -3 and only increases
the conservative generated damage endpoints by four in total. Prototype zeros
are not live weapon damage; `db.c:create_object` generates it from load level.
No acquisition trip or weapon switch has been authorized from that report alone.

The scheduled local commit check rejected a reviewed partial patch before
staging (0.631 seconds of command execution). No commit, push or merge occurred,
the index remains empty, and all worktree changes remain saved. The ignored
`runs/local_commit_attempt.json` records the failure and a conservative next
eligible time of **2026-11-15 9:02:42 PM Pacific/Auckland**. Do not retry sooner.

### Expert Teachers And Refusal Loops

DD4's `do_practice` accepts NPC teaching knowledge above 100, then caps the
resulting player proficiency at 100. `practice_gain` now follows that rule
instead of rejecting expert teachers outright. Source ratings 105 and 110
produce legitimate gains; teacher-base level, prerequisites, practice balances
and route access still apply. This does not open a higher-level trainer route.

Runs **24898**, **24899** and **24901** repeated the croupier's lucky-tier
refusal without combat or XP. The history repair mistook accompanying "tank"
commentary for an HP veto, even though the generated stop allowed only +1
and did not accept the +2..+5 lucky tier. Repairs now require the actual current
stop to accept that tier before changing historical viability. Refusals and
losses are preserved when it does not. Run **24902** selected a different
target, the Secretary **30217**, and entered combat under Sanctuary; this proves
the repeat-selection loop was broken, not that the new hunt succeeded.

That Secretary fight withdrew on observed command-lag/own-health evidence:
1,504 partial XP minus the 1,480 flee penalty, **24 net XP**, no kill. Its exact
level-46 loss remains closed. Run **24903** found Mr. Teece but live consider
said "no match for you"; the below-band refusal was correct and unrelated to
the additional HP comparison. Run **24904** replenished flight. Checkpoint
**79977** records level 46, **2,131,126 XP**, safe at healer room 3054. Expert
teacher and repair cases compile but remain unrun under November 14's spent
regression allowance. The normal campaign command resumed the sand worm/mouse
circuit; its result must be read from completed evidence, not assumed.

Run **24905** killed sand worm **39004** for **3,812 XP**, returned safely and
recorded 14 acknowledged combat commands, 11 timed wake-ups and no timeout.
It reached mouse **39011**, but the mouse's source-only say/emote greeting
excluded it from the +2..+5 live tier even though the route was already
admitted. The separate `greeting_display_programs_only` proof now recognizes
one to four bounded greet scripts, each with at most eight nonempty say/emote
commands. Unknown commands, control flow, embedded line breaks and other
triggers fail. This does not change existing echo grammars or grant a route:
`do_say` can trigger another room mobile's speech program, so existing hazard,
loadout, isolation and loss checks remain mandatory. The saved real circuit
now produces a mouse stop with `allow_lucky_consider=True`, maximum offset 5,
the same armed identity and isolation requirement. New cases are saved unrun;
a fresh completed live fight is still needed to prove the change.

The same live-tier inconsistency affected plain multi-room populations. The
saved croupier candidate passes `plain_bounded_population` with two unequipped,
unspecial sentinel resets in distinct rooms, but was not labelled capacity
research. Level-tier eligibility now reuses that audit independently of the
ranking label. Its two saved-source stops both accept lucky consider through
+5 while retaining exact identity, isolation and a one-target maximum. Existing
negative consider, actual loss, route and provisioning checks still apply.

Run **24906** found only a below-band living shadow. Run **24907** withdrew from
dwarven gambler **20515** for **1,480 net XP lost**; preserve that level-46 loss.
Runs **24908-24909** then exposed a missing preparation handoff: the invisible
Alchemist's required-loot route prepared flight but not detect invisibility.
The live perception gate correctly returned without a kill. The consumable
runner now requests the existing see-invisible shop preparation for candidates
that need detection, retaining actual purchase, funding, effect confirmation
and return checks. This is implemented and compiled, not yet live-proven; new
parameterized cases remain unrun under the daily regression limit.

Run **24910** also escaped Athena without a kill, losing **894 net XP**; keep
that carrier loss closed. Runs **24911-24912** exercised the new detection
preparation: **24911** quoted 207 copper, bought the yellow potion, quaffed its
exact instance and confirmed detect invisibility. However the shared shop
controller took its standalone see-invisible logout branch, so neither run
observed its carrier endpoint. These runs remain failed/unachieved, not resource
successes. The verified-detection branch now logs out only for a standalone
task; a continuing fastwalk falls through the existing water-breathing check
and live-affect handoff. Failed purchases stop immediately. Cases cover both
completion modes and the unverified-water block; they compile but are unrun.

Run **24913** proved that the corrected detection handoff reaches Hermes
**903** and starts combat. It withdrew without a kill or Sanctuary object,
for **319 net XP lost**; retain this exact loss. Run **24914** then achieved
its coin-stash funding objective and returned safely. Checkpoint **80022** is
level **46**, **2,132,245 XP**, full HP/mana and confirmed logout at healer
**3054**, with **1,211 copper-equivalent** carried. The late block since
**79950** gained **1,143 net XP**, not another level.

The bank fallback missed run **24875** because the ordinary runtime segment
tail no longer included it. Its complete command-local withdrawal reply proves
132,614 copper-equivalent remained banked. Funding selection now retrieves
only the latest bank phase within the existing 256-segment bound, then applies
the unchanged receipt checks. A newer failed/running visit or no bounded result
must not resurrect an older successful tail receipt. Cases for all four
outcomes compile but are unrun. This is a selection repair, not a claim that
a new live withdrawal occurred; **24914** used the earlier selected coin route.

## November 14 Protection Replenishment

The later continuation found two interacting selection faults. Unrelated
protection losses suppressed carrier recovery, and an old Moria acquisition
receipt could rename a freshly selected independent carrier. A prior confirmed
acquisition now supplies a bounded preference (at most eight distinct source
stops), not combat permission. Each candidate goes through the existing current
reset, effect, loadout, route, exact-loss and live-gate pipeline. Only the
already supported plain, adept and exact audited fire-carrier shapes enter
this preference. A changed/unknown object receipt cannot launch it. Moria
identity restoration now applies only to its own objective, not another carrier
or an ordinary XP hunt.

Replenishment is a resource cycle, not a once-per-reboot opportunity. The
completed result records `acquisition_segment_id`; a later consumed-object
cycle must have a newer confirmed acquisition than the prior attempt's
`previous_acquisition_segment_id`. Pending/failed attempts and exact carrier
losses remain closed. Saved cases cover real-source re-audit, terminal failures
elsewhere, malformed/stale receipts and cycle boundaries. They compile but
remain unrun under November 14's spent regression allowance.

Run **24917** exercised the corrected croupier +5 plan, reached combat and
withdrew: **483 net XP lost**, no kill. Runs **24915-24916** had no XP progress.
Run **24918** then selected the previously successful sewer dragon **7040** in
room **7428**, killed it for **280 incidental maintenance XP**, and explicitly
got and held Red DragonOrb **7303**. Checkpoint **80035** records full healer
recovery, **2,132,042 XP**, ten charges, and acquisition segment **24281**. This
proves the selection/dispatch/loot path, not another level or an endlessly
repeated resource cycle. Run **24919** completed detection preparation for the
next XP hunt; subsequent combat evidence belongs to its own completed run.

The training review found that cast success is `65 + learned / 3`, with spell
damage using character level; 48% flamestrike gives about 81% basic cast success,
not 48%. The Kerofk priest can teach the known spell (teacher base 20, capacity
80), but the present fallback only searches the character's own distant class
teacher. Cross-class trainer expansion and higher proficiency goals are not
implemented by this review; no practices were spent or new trainer route
authorized. Protection replenishment was the more immediate live blocker.

### Circuit Consider History

The mouse's level-46 lucky-tier refusal belonged to parent worm run **24905**.
Direct phase lookup could not find it; the ordinary runtime tail had also
omitted that older trip. Circuit repair now requires the parent's explicit
child record and source revision, identical start/end character, class,
subclass, level and boot, unchanged cumulative losses, and the child's own
recorded refusal. Discover at most eight relevant parent snapshots from 256
thin headers. A parent fight does not count as child combat; a command in the
child's room (or with unknown room context) still blocks repair. Current exact
losses and the executable lucky-tier gate remain authoritative.

The read-only reconstruction identified **24905** without altering its result.
The normal campaign then persisted the repair and selected mouse **39011** at
checkpoint **80066**. This is live startup/selection evidence; it is not yet a
new kill. Saved cases reject changed identities, sources, levels, losses,
combat boundaries, missing children and unlinked outcomes. They compile but
remain unrun under the spent daily regression allowance.

Run **24921** killed another worm for **3,797 XP**, objective achieved and safe.
The following **24922** made no kill. Run **24923** made no objective kill and
recorded only 10 net XP; **24924** completed flight preparation. Those low/zero
progress visits remain part of the whole-session accounting.

Run **24925** reached mouse **39011**, passed live consider and brandished the
verified orb before combat. It withdrew without a kill for **541 net XP lost**;
preserve that exact protected level-46 loss. This proves the corrected child
handoff reaches combat, not that it is a productive hunt. Run **24926** killed
goblin **4520** for 110 incidental supply XP and acquired the source-backed
detect-hidden resource **4558**. Checkpoint **80072** records **2,135,418 XP**,
full HP/mana/movement, healer logout, 716 copper-equivalent and eight Sanctuary
charges. Total since **80022** is **+3,173 XP**, including 390 maintenance XP.

The gear report identifies real output upgrades but does not authorize them:
Snake-eyes carries head/finger/floating upgrades, Cutter and the helmsman a
five-damroll shield, and the Cyclops thief damaging/accurate gloves. Low-level
Thalos golems offer smaller armor improvements. Their exact source routes,
specials, existing losses, carrying room and live acquisition still need
review. The Astral hammer remains a hitroll tradeoff, not an automatic upgrade.
Do not relax target-HP admission or erase losses to pursue gear. Combat strength
and useful teacher access are the next practical blockers; no new gear or
lesson is claimed from this report.

## Commentary And Discord

At the start of every assistant turn, before commentary or other tool work,
append the newest visible user message verbatim to `DEVELOPMENT_CONVERSATION.txt`.
Repeat this after interruptions and context compaction; do not assume the newest
visible message is already recorded.
Append every visible assistant update and final response before displaying it.
Do not append internal goal continuations or injected environment context as
user speech. Never rewrite this append-only file or replay historical entries
to Discord.

Append the exact message through standard input. The helper reads the pipe's
UTF-8 bytes directly, avoiding Windows Python's default console encoding:

```powershell
$body = @'
Exact update text
'@
$body | python tools/conversation_log.py append --speaker "CODEX COMMENTARY" --body-stdin
```

For a live Codex update, add `--quiet` to the append command. Display the
timestamped update once in chat, then record that same body once in the
append-only log; pipe the command to `Out-Null` and do not also use
`Write-Output $body`, because command output plus the chat update duplicates the
post. The logger also rejects nested timestamped assistant bodies and an
assistant body repeated in its recent 128-record window; do not bypass either
rejection. Keep the
here-string assignment inside the same PowerShell command that
invokes the helper; variables from the surrounding tool wrapper are not
available to PowerShell. Without `--quiet`, the helper prints its generated header for callers
that need to publish the returned record themselves. Use `USER` for user turns and
`CODEX FINAL` for the final response. Headers must be exactly:

```text
[YYYY-MM-DD h:mm:ss AM/PM NZST] CODEX COMMENTARY
[YYYY-MM-DD h:mm:ss AM/PM NZST] USER
[YYYY-MM-DD h:mm:ss AM/PM NZST] CODEX FINAL
```

Use current Pacific/Auckland time, literal uppercase AM/PM, and the helper's
timezone label. Never nest another timestamped speaker header inside a body.
Provide informative progress updates about every 30 seconds during long work.
Validate format with `python tools/conversation_log.py validate`.

Keep the separate streamer in `--new-only` mode with historical replay disabled.
Do not kill it during gameplay-worker cleanup. Never reset its offset to zero.
After a logging repair, verify the new USER record exists locally, the streamer
logged successful USER delivery, and its queue is empty at the source EOF.
An absent local USER record cannot be repaired by restarting Discord delivery.
The preserved instruction archive contains the full no-rewind, timestamp,
content-deduplication, and at-most-once delivery contract; consult it before
editing the streamer. Launch background helpers hidden, without console windows.
Read live results before drafting numerical claims. Do not combine an unread
result query and a guessed commentary reward in one tool call. Timestamped
updates describe evidence already returned; correct mistakes append-only.

## Authorization And Fail-Fast Behavior

### Combat State Ownership

DD4 source `merc.h` defines `POS_FIGHTING` as 6, and `update.c` reports that
position through `Char.Vitals`. Fresh valid positions 0-7 update the root
character state's combat flag; only 6 marks fighting. Valid nonempty
`Char.Enemies` also marks combat, while a valid empty snapshot clears combat
and the target. Explicit nonfighting positions clear the target too.
Do not derive target identity from posture or an ambiguous enemy list.
Missing/malformed position or enemy data does not prove a transition;
partial vitals must not revive combat from a retained position 6.

Runs **16850/16852** exposed position 6 and nonempty enemies persisting with
`in_combat=False`; neither observation previously set the flag. This live-state
correction leaves the 20% plain-target trigger, controller admissions and loss
ledgers unchanged. Historical evidence is not rewritten. Focused cases compile
and await October 11's regression batch; fresh live proof is tracked separately.
Run **16862** observed position 6 and `in_combat=True` at **762/767 HP**, then
position 4 and `False` at the healer after a **1,628-XP** kill. Its objective,
safety and farewell confirmation were independently positive. This verifies
the live flag transition; it does not replace the pending negative-case tests.

Run **17229** reached **153/831 HP (18.4%)** with the target at 121 HP. The
near-dead finisher calculation lowered its temporary withdrawal floor below
20%, despite a 138-HP source critical estimate; the next hit dropped Dorrik to
27 HP, where the ordinary reserve restored the 20% trigger. For source-proven
unarmed targets without specials, the 20% floor is now applied before finisher
grace. A focused case reproduces those exact values; compilation passes, and
the case awaits the next daily regression batch. Do not retry this target
without the verified regression and fresh policy admission.

### Food Supply And Failed-Fight Baselines

At a noncombat healer checkpoint, a needed current-band food reserve may prefer
the existing Bakery executor when fame is known and nonnegative, the current
source pie is plain nonpoisonous food, and the selection budget includes two
source-cost pies plus the current flight allowance. Preserve city-shop blocks,
cooldowns and the no-consecutive-restock rule. This is a purchase preference,
not a price guarantee: live stock/quote, capacity and route checks still decide
the order. Unaffordable or blocked characters keep the existing source-food path.

Before an exact-source withdrawal, retain a compact output estimate from the
currently worn combat gear. Commit it only on the matching explicit XP-loss
event. Target-HP evidence keeps the old planned ceiling separately and uses the
higher baseline for improved-output revalidation. This is source-estimated
output with observed equipment, not measured damage. Legacy same-weapon health
or damage-window failures lacking it cannot reopen merely because a later
checkpoint wears combat instead of recovery gear. Keep consumed markers and
all old losses; do not rewrite historical rows or alter combat permission.

### Inventory And Combat Text

DD4's source `update.c` builds Telnet inventory strings using colour-converted
descriptions. Raw ANSI escapes can make the captured JSON nonstandard. Stored
item-objective parsing removes complete ANSI sequences before standard JSON
decoding, preserving quantities and distinct entries. Incomplete escapes and
malformed structured JSON are not item evidence; raw `[#ID]` descriptions remain
single entries. Numeric zero is not the default quantity one. An exact affected
completed summary may be repaired with `refresh-run-summary RUN_ID`; never
rewrite transcripts or refresh the whole database automatically.

Direct attack lines may contain a possessive mobile name, such as
`Teacher's last student misses you.` This is not an attack by `Teacher`.
Disambiguation requires the complete current source name; ordinary possessive
weapon/spell attack messages and genuinely additional attackers stay in force.
Parsing does not authorize a fight, identify an instance, erase XP loss, or
reopen a failed policy. New cases await the next available regression allowance.

### Bounded Logout Confirmation

Normal starter workers must read after a dispatched `quit`, for at most five
seconds, and capture the exact complete source reply
`You bid farewell to the Dragons Domain.` in `logout_confirmation`. The
session owner retains a compact receipt; canonical events retain final text
and GMCP. Split text, ANSI and complete DD4 prompts are handled incrementally.
Chatter does not extend the deadline. A refusal, bare EOF, partial farewell,
send/read failure or timeout is visibly unconfirmed; never reconnect, repeat
`quit`, or issue a probe to repair it. A confirmed farewell proves logout only,
not objective completion or a safe hunt. Death and XP-loss outcomes still win.
Cached historical summaries without this receipt remain unknown; do not
rewrite history or invalidate every summary to populate the new field.
The exact failed-underwater cleanup remains separately source-gated; neither
confirmation path permits a new field endpoint or logout in Purgatory.

Run 16744 exposed a duplicate-login filter fault, not incorrect DD4 carrying
data: flight expiry refreshed identical room metadata except exit costs while
retaining `arrival.kind=login`. The raw packets correctly reported 38/38 and
five loose vines after a drop, but quarantine suppressed them. Admit only a
complete, prior-matched same-room snapshot with valid nonnegative integer
cost-only changes; retain destination, door/state, identity and all malformed/
foreign guards. An existing quarantine is never cleared by this allowance.
The room baseline is connection-local and copied, not shared with event data.
16745 verified acknowledged 38/38 to 37/38 cleanup and flight renewal, not the
exact expiry boundary; its focused cases await October 11.

The ready, registered Midgaard fountain preflight at room 3005, water steps
1-3 and outbound index zero, may retain applied combat gear through movement-
only checks. Require the source recall origin 3001, readiness, existing health/
mana gates and no return lifecycle. No new travel or combat permission follows.
A return at healer 3054 retains already-applied recovery gear after waking;
ordinary recovery readiness still gates completion. 16747 verified fountain
fill/drink without swaps and a single healer sleep, then stand/save/quit.
The original near-full-movement fountain boundary remains unproved live.

An explicitly registered required-loot stop may inspect one reset-ambiguous
carrier instead of demanding a second mob that may not be present. Require an
exact live instance, the existing source identity check, a unique source object
name, and an audited worn reset sufficient for the missing quantity. The
five-second `look #<instance>` reply must finish at a prompt and show the exact
source description, target health, and the required item in equipment; neither
description mentions nor peeked inventory count. Bind the receipt to room,
instance, mobile, visit, missing quantity, level and boot; expire it after
twenty seconds and invalidate it on movement. Keep the real mobile count and
every crowd, consider, health, combat, loot and retry gate. At most eight
inspections run per session, with no same-instance/visit retry. Only the daycare
ring stop opts in. October 10 cases compile but await the next daily batch.
Required-loot cleanup fixes its session budget from the initial observed item
deficit, including any existing overload, with at most eight disposals. Keep
the source-identified redundant-item selector and drop/sacrifice/inventory
acknowledgements. A missing capacity change never expands that fixed budget;
departure still requires fresh sufficient capacity. Run 16700 exposed the
old one-item budget stopping at 38/38 after repairing a one-item overload.
Each cleanup phase now accumulates its own bounded reply rather than using the
latest Telnet chunk. Require complete drop/sacrifice lines and inventory's
header/count footer; healer chatter is not an acknowledgement. A pending phase
keeps the route open and times out visibly after five seconds. Run 16706 exposed
the old premature logout; run 16710 subsequently confirmed a delayed flask drop,
sacrifice and inventory audit before actual departure.

`HealerPouchStorage`, owned by the recovery controller, may first audit an exact
structured worn pouch at room 3054. Only an observed empty pouch admits one
source-candidate potion group, at most four individual placements, bounded by
the worst candidate weight and source container capacity. Require each exact
put reply and a fresh text/GMCP count reduced by the acknowledged quantity.
Every reply has a five-second deadline. A nonempty pouch or ordinary release/fit
refusal ends this optional storage attempt without claiming a slot. Record
`storage_only`: ambiguous potion effects remain unknown and quaffing is not
authorized. Do not nest containers or alter the combat reserve ledger from
storage alone. Run 16710 confirmed two clear potions stored and 39/38 to 37/38
capacity before one redundant flask was sacrificed; the water skin and gear
remained. Ordinary source-unique drink-vessel cleanup requires another carried
vessel whose every source variant is plain refillable water. Retain the last
water vessel of each prototype; an ordinary nonwater vessel needs no reserve,
including its last copy. Poison, ambiguous prototypes, protected gear and
keyword collisions remain excluded. Contents are not inferred safe to drink
from prototype values; only disposal is admitted. A colliding default word may
use another actual source keyword only with complete source-known inventory
and no matching peer prefix. Unknown descriptions close this selector. Run
16849 live-confirmed `drop shot`, sacrifice and 38/38 to 37/38 carrying relief,
then purchase/use of flight for 141 copper, without changing the audit budget.

`HealerCarryingCapacity` now owns the shared required-loot and flight-shop
preflight. A flight purchase normally reserves one free item slot before
leaving room 3054; existing overload counts against the fixed eight-disposal
maximum. If no ordinary safe relief item exists, one exact source-identified
worn Mud School diploma (#3715) may be recorded as a destination relief plan
only when dropping it covers the measured deficit. At the Magic Shop, require
DD4's exact capacity refusal before removing and caching the diploma, retry the
purchase only after the acknowledged drop, and restore it before departure.
Preserve the last carried food reserve; only surplus food or urgently needed
food may be consumed for capacity. The plan is not a free slot until the live
shop rejection and recovery flow confirms it.
After an aborted preparation starts healer logout, the logout controller owns
recovery instead of alternating with generic departure recovery. Ordinary field
returns retain the 90% movement reserve, runtime-boundary returns retain their
separate 40% reserve, and health/mana requirements remain unchanged. Sleeping
waits continue reading live output; a preparation correction does not reopen
the failed route or authorize a new departure.
Drop/sacrifice/inventory replies and five-second state confirmation remain
mandatory. Record the compact cleanup receipt and separate purchase failure
causes. Capacity is not insufficient money. For a legacy purchase outside the
eight-segment tail, inspect one exact latest purchase among at most 256 segment
rows and fewer than 256 complete canonical events. Require actual `buy light`
carrying replies and reject funds/reputation evidence; preserve run/segment
provenance and all cooldowns. Failed historical rows remain unchanged. These
new cases compile but await October 11's regression batch.

Runs 16720-16723 exposed four empty liquidation visits after the successful
sale in 16719. The retained signature was unchanged, but subtracting the worn
I.Q. Vine namesake from its baseline made carried duplicates appear new.
Compare the exact signature first; apply the legacy inventory-to-worn
adjustment only when it differs. A later changed signature may reopen sale
planning, never a blind sale of an ambiguous instance. Fresh selection after
this correction left liquidation and resumed gear/XP work; the focused cases
compile but remain unrun until October 11.

Newly retained duplicates then exposed a separate completion fault in
16728-16729: no-sale plans kept the previous signature. Record
`campaign_liquidation_completion`, bound to the exact run, only after finished
planning at healer 3054 with no pending/rejected action, failure or runtime
interruption. Its completed retention may update the baseline without profit
or an achieved objective. Legacy no-op repair must preserve this explicit
receipt. Run 16730 verified the new baseline and fresh 16731 resumed XP work.

Runs 16750/16752 exposed repeated vine-shop trips: the refusal pattern excluded
internal full stops and missed `an I.Q. Vine`. Share the pattern in `shops.py`
between live policy, bounded historical recovery and reports. Accept refusals
after value or sell, requiring a complete line from the recovery controller's
2,048-character command-local buffer; clear it on the next shop command and
after a recorded refusal. Preserve existing alternate-buyer, donation and
retention checks. Standalone 16763 sold one vine for one copper, recognized the
next refusal, and immediately returned instead of retrying that buyer. Its
alternate route failed after three city waits: failed/unknown/safe, not completed
cleanup. It saved at healer 3054 with no combat or XP change. Split-packet and
negative cases compile but await October 11; no historical summaries were rewritten.

Run 16702 falsely called the intended buck an extra attacker because the
dispatched keyword was `deer` but combat text said `The buck`. Ordered GMCP
recorded only source mobile 19039 in room 19132; flee lost 592 XP, offset by
97 damage XP. Keep execution success, objective not-achieved, safety loss and
the closed policy. The combat controller may reconcile that flag only for an
already-opened, unfinished fight with one raw current-room enemy, matching
source VNUM, canonical name and room description, the exact registered reset
room, and one selected instance without a conflicting selector. Preserve real
crowds and every combat limit. Record at most eight aliases per session. This
repair compiles but has no fresh live proof; focused cases await October 11.

For source-ranked circuits, record the exact source policy, mobile VNUM,
registered room and current live opponent in the combat controller before a
flee/recall clears identity. Commit that record only after an explicit positive
XP-loss event. Successful earlier kills must not clear the failed stop, even
when partial damage XP makes the trip profitable. Across connections, compare
`campaign_xp_loss_total`; identical per-run penalties are separate losses.
Missing legacy identities may be reconstructed only from linked runs in the
existing eight-segment tail, at most four loss events and 128 preceding events
each. Require exact GMCP enemy, actual room/arrival and dispatched withdrawal;
shared names, absent targets and safe aborts never prove a failed fight. Keep
secondary-stop counts when phase indexes omit their parent circuit. This repair
closes losses; it creates no new retry permission. October 10 replay cases are
written and compile, but remain unrun until the next daily batch.

Departure `where`/adjacent scans retain `fastwalk_recovery_ready` until the
first actual outbound command. At the exact verified safe route origin,
already-applied combat gear may remain during movement-only checks when health,
mana and other readiness gates pass. A blocked scan still aborts normally;
this is neither a field sleep location nor relaxed combat/travel admission.

Automatic source absence/no-progress fallback is not a route-program retry.
Do not derive `allow_route_program_retry` from a cooldown-rotation flag; doing
so can reopen an obstructed productive route before the final dynamic-hazard
guard has enough context to stop it. Preserve the saved route result and useful
kill history, select other candidates normally, and retain the final guard.
Only an existing exact, source-audited revalidation may reopen that
source-validated preflight. `--retry-stalled` rotates the frontier but does not
grant route-program retry permission.

When a completed area-reset boundary ages an exact legacy protection-recovery
fallback, the selector may reopen that one unattempted fallback. A dispatched
fallback remains closed after a no-progress result, and XP-loss evidence always
wins over reset aging.

For a recently productive plain hunt, a completed clear city observation may
arm one exact-policy/level/boot clearance even when a different policy spent
the legacy global receipt. Require a current-version linked summary-confirmed
objective kill in the existing eight-segment tail, unchanged source and total
losses, current XP matching that recovered hunt's end, and a later successful
no-travel three-wait block followed by a changed clear locator. Preserve the
old receipt under `superseded_clearance`, retain the blocked-policy ledger,
and persist `campaign_productive_city_clearances` before opening the worker.
Admission still checks route, provisions, source output, useful XP, flight,
health, crowd and loss; repeat fresh locator, exact instance and consider live.
The receipt binds the prior result and XP/loss to its pending ledger entry and
is consumed before dispatch. This cannot reset a spent same-policy clearance,
combat loss, failed target check or changed source. Cases are saved for October
11, not an additional October 10 regression batch.

Live run 16671 consumed that productive receipt before connecting and crossed
the formerly blocked city route. Its source-12041 citizen had 915 HP versus
624 on the previous successful instance. The fight withdrew at the 20%
trigger, reached 18.98% HP during flee, lost 551 XP before damage XP reduced
the net loss to 188, and returned recovered to the healer. Record safety=loss;
the combat failure and same-policy clearance remain closed. Run 16672 acquired
no sanctuary; 16673 renewed flight for 141 copper. Checkpoint 49712 is level
30 with 662,990 XP and 6,060 remaining to 31. No level transition is proved.

`combat_actions.preferred_timed_damage_skill` compares already-admitted kick
and headbutt using positive observed proficiency and DD4's strict percent roll.
Both have blunt/nonmagic resistance flags; successful headbutt waits six
seconds, failure three, and kick two. NPC ordinary attacks are not suspended
by this wait. Include second headbutt only from its observed proficiency.
Planner and live dispatch share the choice; unknown inputs keep prior ordering.
`CombatCommandWindow` recognizes only the exact target's damage acknowledgement,
splits complete prompt prefixes, and retains those waits plus one input pulse.
The failed-headbutt short wait requires its exact miss without a preceding
success message. This never reopens losses or changes encounter admission.
At checkpoint 49713 the next launch stopped before login because the source
frontier remained unavailable and the sanctuary recheck was spent; there was
no new run or XP change. Timing/ranking cases compile but await October 11;
the new rotation is not live-proved yet.

### Verified Level-31 Transition

Checkpoint **49727**, last run **16680**, records Dorrik at level **31 Knight**,
**670,744 XP**, **57,556 XP** to 32, **18 QP**, alive/noncombat at healer 3054.
Runs **16674/16675/16678/16679** killed the Catacombs sentinel and Mirror Realm
buck for **2,074/2,231/1,591/1,858 XP**, respectively. All four record
success/achieved/safe with no flee or XP loss. Including maintenance visits
**16676/16677/16680**, the seven-run total is **7,754 XP** in **727.90 connected
seconds**, approximately **639 XP/minute**; development/planning is excluded.
Selling and banking have unknown objective outcomes; the ring objective was
not achieved. Do not relabel these maintenance runs as successful item goals.

`greeting_echo_programs_only` admits only greeting triggers, numeric percent
conditions, at most four programs/32 commands/four nested random branches,
balanced control flow, and non-CHAT local echoes. Unknown commands, casts,
attack/transfer actions and malformed scripts remain closed. It is a source
behavior proof, not route or combat permission. The sentinel retains the exact
existing bouncer route and fresh source/loadout/identity/isolation/consider gates.
Its independent contract was never part of the failed three-target parent.
Programs containing `mptransfer`/`mptrans` for `$n`, `$t`, or `all`, including
the nested `mpat ... mptransfer` form, are hard source target/route hazards:
they can invalidate the planned room and target identity. Pure `mpgoto` moves
the mobile itself and is not treated as a player transfer. The live runner also
aborts and records the route if a forced relocation is observed.
`completed_single_target_hunt` accepts only the exact current-version safe,
achieved linked summary with one useful source-tagged kill, matching boot and
recorded start/end source revisions, terminal level, and unchanged encounter
loss totals. An opted-in one-level
transition also requires its exact summary levels and observed gain, preserving
the original source-policy tag. Later unrelated losses cannot erase that
success; current/prior exact target quarantines remain authoritative and loss
totals cannot rewind. A completed productive independent hunt may repeat beyond
the initial three-kill discovery cap, retaining its one-kill visit limit and
every fresh source/live check. Absence, crowd, loss, or failed objective cannot
qualify. Historical rows and parent failure ledgers are not rewritten.
Each bounded stale-consider rotation may recheck a capped target only when the
same productive-repeat helper admits its exact policy from meaningful same-boot
XP evidence and no terminal loss. An empty rotation is a selection aid, not a
reboot-sized quota: a later bounded invocation may start another target-rotated
pass. Preserve the old negative result; the fresh live `consider` remains
authoritative, and this exception never reopens a loss, crowd, route hazard, or
identity failure. After a live absence locate, the exact target yields to a
different hunt until that dispatch releases the rotation.

`hunt_efficiency.py` compares at most eight linked completed visits using their
actual net XP and full run duration, including safe zero-progress visits to the
same route. It deduplicates runs and rejects old summaries, malformed timing,
unlinked outcomes and token rewards. These are route-selection observations,
not a controlled class-balance experiment or combat permission. A proven
registered current-band hunt may compete before the generic frontier is empty;
an unmeasured generic choice does not automatically suppress the proven route.
An already-selected multi-kill circuit keeps control: single-target receipts
cannot establish its comparable rate or justify replacing it.
Persist the selected comparison's run IDs and rates in its segment start.
Fresh complete source route/loadout audit may admit historical success recorded
under an older revision; its own start/end revisions must still match, and no
historical revision or loss ledger is rewritten. Food, recovery, flight,
QP/fame, current source and every live targeting/consider/output gate remain.

Run **16679** live-confirmed the level gain, 26 HP, 17 mana, 10 movement and
3 physical/2 intellectual practices. Repeated kicks were dispatched in these
fights; this does not establish comparative balance or prove every timing edge.
No sanctuary, optional quest, reboot wait or roster rotation was needed.
Compilation passes; new script/selection/timing cases await October 11, not
a second October 10 regression batch. Next: fresh level-31 training and useful
XP toward 32. HERO and full class/race coverage remain unproved.

### Area-Local Recall Recovery

DD4 `do_recall` uses the current area's `#RECALL` when recall index zero is
selected. `recall set 0` does not force Midgaard, and word of recall uses the
same rule. The Ota'ar Dar market's destination is room 27347. Run 16462
confirmed Dorrik's Knight identity but ended there after the old return routine
incorrectly expected Midgaard. It gained no XP and incurred no loss.

The maintenance-only `AreaRecallEscape` owns one bounded return attempt. From
27347 it may visit shop 27331 via 27341/27336/27337/27332 and purchase exactly
source object 27292 (goblin shark pie) using a live quote, exact selector, level,
inventory confirmation, and 100-copper reserve. Its spell level is 40; the
object's usable level is 30. Source mobile 27246 is a separately audited
economic risk on this shop route: non-aggressive, unprogrammed, `spec_thief`
only, with the exact ordinary loincloth/dagger resets. No combat is authorized.
Any other diagnosed shop-route hazard closes the exception.

Require independently verified water breathing or an explicit `update.c`
survival exemption, fresh flight, at least 95% HP, 30 movement, observed infravision (or
clairvoyance), and observed sanctuary before the escape. Follow the exact
source/live exits 27347 up 27647 up 27132 up 27071, scanning before each dark
destination. Reject every one-room sighting, unknown/incomplete scan reply,
closed exit, hidden/invisible source attacker, changed attacker set, changed
reset or special, and source/live route mismatch. Distant sightings do not
occupy the immediate destination. Only at source-recallable Undersea room
27071 may the routine recall to 3001 and continue north to healer 3054. Cap
the routine at thirty commands and every response at five seconds. Store
`campaign_area_recall_escape` evidence. This is recovery, never hunt admission;
live success remains unproved until an observed healer return.

### Ota'ar Dar Favour Gate

The Ota'ar Dar gladiators hold a character in the arena until all five distinct
favours have been collected. Treat this as a hard live gate, not a normal
arena completion condition: retain arena control through the remaining
gladiator sequence and do not issue the exit route, generic recall, logout, or
maintenance detour while any favour is missing. Source objects **27481-27485**
are `ITEM_TREASURE` (type 8), not `ITEM_KEY` (type 18). DD4's save routine
excludes keys but writes carried treasure, and both `quit` and a controlled
reboot invoke that save routine, so a completed save preserves these level-30
tokens. Keep them directly in inventory because the gatekeeper's `carrying()`
check does not search inside containers. After reconnect, revalidate each
older receipt with a fresh inventory listing whose description uniquely maps
to the source VNUM and source item type; receipt-only evidence from an earlier
boot remains invalid. The source gatekeeper still requires
one favour from every gladiator type before transferring the character to the
staging zone. A live fight that ends in death before a favour is saved is not
evidence that the character was released or that the exit route is valid.

### Bounded Economic Route Specials

During protection recovery, an ordinary fallback may retain a route whose only
special is a source-audited passive economic `spec_thief`. Require the exact
`route_economic_hunt_mobile_vnums` receipt, the complete source reset audit,
and no more than **1,250 copper-equivalent** carried at runtime. Recheck the
source identity and purse before dispatch. This permits bounded transit only;
it never authorizes combat with the thief or crossing another special, script,
or attacker.
For the fixed Mirror Realm route population, a plain endpoint may use the
source-ranker allowance for ordinary non-spell reset gear on those exact five
VNUMs. Keep the complete one-reset audit and the original economic rejection;
special endpoints, other areas, spells, scripts, and combat-capable specials do
not receive this allowance.

### Source-Refresh Plain-Target Retry

An upstream source revision does not reopen old combat losses by itself. After a
complete current-source audit, selection may create one explicit
`campaign_source_ranked_source_refresh_revalidation` receipt for a fixed-room,
unarmed, unprogrammed singleton with one or two same-boot losses recorded under
an older source revision. The receipt records the exact target, route and
source reset, preserves the historical loss, and still requires fresh live
identity, isolation, `consider`, output, health and recovery checks. It is
consumed before connection and closes after the attempt, whether or not a kill
is achieved; it must never become a retry loop.

The same source-refresh distinction applies to the exact Moria Sanctuary
resource route. When the old fixed-reset attempt is tied to a different source
revision, the current source must still prove mobile **4055**, purple potion
object **4050**, reset room **4064**, and the existing route/loadout contract.
The runner may then consume one
`campaign_moria_sanctuary_source_refresh_revalidation` receipt before a
required-loot attempt. The old failed attempt and all protection-loss evidence
remain intact; a missing potion closes this recheck and does not create a
combat retry or a loop. When that exact current-source receipt closes as
`no_object`, the source-confirmed second Moria reset at room **4071** may be
used once as the distinct
`source-ranked-sanctuary-moria-fixed-reset-4071-2-100` handoff, even if an
older area-reset marker is unavailable. Consume that attempt before dispatch,
retain both receipts, and keep it strictly required-loot-only.
If room **4071** already has an older attempted or acquired receipt under a
different source revision, do not replay it. A fresh current-source audit may
consume one `campaign_moria_sanctuary_second_source_refresh_revalidation`
marker, bound to the closed room-**4064** `no_object` receipt, before the same
required-loot-only handoff. Close the marker on absence or acquisition and
preserve the older room-4071 evidence unchanged.

Trainer visits record `subclass_selection` independently from execution and
safety. A requested subclass in the profile is not proof: require the final
observed character identity to match. New recovery and reporting cases are
queued for October 8; do not exceed October 7's spent regression allowance.

Run 16463 reconnected in Purgatory before using this new escape controller.
It retrieved the corpse, exited the portal, restored and audited gear, and
returned to the healer at 696/702 HP. The gap from the previous checkpoint was
-226 XP. `update.c` drains air and applies drowning damage in sectors 8/12
regardless of flight; that is a likely cause, not directly observed death text.
Do not label the old foreign-room disconnect a safe recovered return.
On a live failed noncombat room-27347 session, only the exact source/no-mob
logout gate may send `quit` once before closing, with five seconds each for
send and farewell confirmation. Record `failed_local_recall_logout`; retain
the original failed execution. `do_quit` saves the character. Missing source,
combat, enemy evidence, an uncommandable character, or Purgatory forbids this
cleanup. It is not generic permission to quit from arbitrary field rooms.

Before calling an autonomous attempt pre-connection or retrying its policy,
check the process list, `show-campaign`, `show-runs --limit 4`, and the exact
transcript/current state. A campaign segment with no `run_id` or zero recorded
commands does not prove that the run issued none. If the worker has stopped,
recover while its segment is still running with
`recover-runs --campaign-id N --character NAME`; this binds a unique matching
run and preserves its measured execution, objective, and safety outcomes. Do
not repeat a target after a live output-budget flee without new source or live
evidence clearing that gate. Failed-segment source-loss repair must merge the
exact starting campaign metadata with the terminal state, and requires a linked
run, nonzero command count, and explicit XP-loss evidence. An orphan or safe
abort cannot create a target quarantine.

Run reports reconcile `completed_kills` from ordered events with the compact
`mob_kills` index. If a recovered or interrupted run has a kill in that index
but not its cached summary, use `refresh-run-summary RUN_ID` to rebuild exactly
that run's summary and reconcile its indexed outcomes; ordinary `report` stays
read-only. Execution, objective, and safety outcomes remain independent.
Campaign segments inherit refreshed run outcomes unless they explicitly own a
campaign-specific objective. Only objective-eligible kills count toward a kill
objective; route-gate and below-band kills remain visible evidence but never
satisfy progression.
Health minima must include ordered `vitals_changed` and `prompt_seen` pairs,
not just full-state checkpoint boundaries. Require each observation's own
valid HP and maximum; do not pair a partial update with a guessed maximum.
This keeps compact storage without hiding damage healed before the end.
Exact run summaries may be refreshed; do not force a full-history rebuild.

Keep the DD4 source checkout at `runs/dd4-source` current with `origin/master`.
Update it only after every live worker has finished and `git status` is clean.
Use a fast-forward update, then parse the full world and verify representative
pilot-route rooms and prototypes before relying on its new revision. The
October 7 refresh moved from **48cb5a6** to **bbd55b1**; parser smoke found
13,052 rooms, 4,125 mobiles, and 6,138 objects. No regression suite was run.
On October 8, with no live worker and a clean source checkout, the source mirror
fast-forwarded from **bbd55b1** to **7953a00**. Full parsing returned the same
world counts. The refreshed source confirms club **1521** has one ground reset
in room **1573**, and the recall-to-reset route is 18 steps / 71 ground
movement, with no flight requirement. Its low-level program hazard is mobile
**3064** (`greet_prog`, `mpkill`); the direct-loot placement now retains the
registered live `where` preflight and route-room list. Live pickup is unproved.
The new source commits also changed stun/fall and undead-aggression handling;
the live server's deployed revision is unknown, so do not count those changes
as live evidence.

On October 10, after confirming no live worker and a clean source checkout, the
source mirror fast-forwarded from **6d77df8** to **971d8e7**. The full parser
again returned **13,052 rooms, 4,125 mobiles, and 6,138 objects**. The refresh
did not change `const.c` or `pre_reqs`; it updates the working source baseline,
not live-server behavior. Those skill-tree files also match the bundled
analysis baseline at **7953a006**, so the class-priority report remains current
through this refresh.

On October 11, with no live worker and a clean source checkout, the mirror
fast-forwarded from **4c039fa** to **26749cd**. Full parsing verified **13,052
rooms, 4,125 mobiles, 6,138 objects, 7,749 mobile resets, and 1,430 object
resets**; the three representative Midgaard, Kerofk, and 36 Chambers rooms
loaded. This commit adds `turn undead` to the Divine Magiks trainer group and
increments `MAX_SPELL_GROUP`; the prerequisite files did not change. The
bundled prerequisite snapshot remains valid for its unchanged data, but teacher
availability must still come from the live learnable listing. Source changes do
not prove the running MUD has deployed them.

Startup productive-history repair uses the already-loaded normalized,
same-boot kill ledger alongside the eight-segment JSON tail. Require an exact
source-policy tag, objective eligibility, useful-band membership, no route-gate
flag, and a meaningful latest recorded kill reward. Maintenance visits cannot
erase older proven hunt identities merely by pushing them outside that tail.
Do not expand historical event or checkpoint reads. Normal loss, current
low-reward, crowd, route, cooldown, and live checks remain authoritative.
After a previously productive route returned before its opener solely for a
missing sanctuary reserve, fresh supply may restore ordinary kill-cap repeat
admission only with an observed viable same-boot result, no target-loss record,
and no absence, crowd, route, mismatch, unattackable, or below-band evidence.
This repairs a prerequisite, not a failed fight or a consumed route marker.
Only that exact repaired prerequisite is removed from the soft no-progress
rotation list; ordinary source and live admission still decide dispatch.
Run 16454 live-proved the repair with a protected Ki-Rin kill, +1,017 net XP,
level 29 to 30, and safe full healer recovery. Run 16455 resumed that checkpoint
in a new process and gained one defense-knowledge percent, without quests.

At healer room **3054**, a live food or drink need with the matching supply
already carried takes priority over movement-rest sleep. Wake, eat or drink,
then resume recovery. A repeated stand/sleep cycle while supplies are usable is
a controller failure, not productive waiting.

October 11 runs **17274/17275** exposed a reconnect gap: GMCP reported hunger **2** at healer room 3054 with six pies carried, but the policy only armed its food need at zero and left on a loot route. `StarterPolicy` now treats hunger or thirst at **8 or below** as a recovery need only at a safe, noncombat healer; at that low threshold it may consume the last carried food. Run **17276** live-verified waking, eating two pies to DD4's “You are full” response, and drinking from the water skin before leaving for the warehouse hunt, which finished safely for **2,305 XP**. `test_low_positive_nutrition_at_healer_preempts_loot_travel` covers the food and drink wake/consume path. The touched Python files compile; pytest is deferred because today's regression batch has already been used.

Combat swiftness estimates consume the revealed GMCP `Char.Stats.swift` total.
DD4's `GET_SWIFT` already includes the DEX and enhanced-swiftness bonuses;
adding either again overstates automatic attacks. `number_percent()` rolls
1..100 and the attack check is strictly less than the score. Use the clamped
score-minus-one probability; hidden/sentinel data grants no inferred bonus.
Digging differs: subtract the practiced enhanced-swiftness contribution, but
do not remove or add the DEX contribution a second time.

NPC normal-hit estimates mirror `fight.c:one_hit`'s level bands: add level/4
below 30, level/2 below 65, otherwise 3*level/4, before the weapon multiplier.
Peak, expected, critical, and sanctuary calculations share that base; preserve
per-hit damage-modifier scaling and sanctuary-before-critical rounding.
For an exact, source-confirmed single unarmed target with no special, ordinary
combat withdraws at 20% health rather than stacking two observed-hit reserves.
This accepts more risk only for that plain-target case; poison, multiple
enemies, explicit stop and route floors, and all live identity, consider, and
damage/output gates remain in force.
`mobile_loadouts.single_weapon_loadout` may extend the independently prepared
single-weapon defense probe to passive singleton wanderers and ordinary reset
armor/instruments. Require one global reset/capacity, exact wield identity, no
aggression, scripts, scavenging or specials, and a complete ordinary loadout.
For common-rank gear, `db.c` uses prototype level minus two: under 40 (or with
the weak flag), `random_qnd` keeps existing affects within 25 percent. Round
positive damage and HP ceilings upward; fixed gear keeps exact affects.
Reject strong/fickle randomisation, unknown/critical/swiftness affects, poison,
spell items and additional weapons. Add damage after the NPC wield multiplier
and before its damage modifier; preserve corrected raw peak/critical and HP
ceilings in the live hunt stops. Fresh training, equipped defenses, full health,
finite damage output, isolated identity/consider, route and loss gates still
apply. Target sanctuary halves ordinary/opening source output before finite
action planning; unmodelled target protection, battle aura and globe close
this new admission. Wandering permission does not widen the eight-room blind search or
reset a saved failure. New regression cases await October 11; this expansion
has no live combat proof. Run 16657 found the Highlander and rejected its
below-band consider, returning to the healer without combat or loss. That
negative evidence stays closed; the later sanctuary correction grants no retry.
`populations.plain_bounded_population` supplies a source proof for the existing
capacity-research isolation check: two to four passive sentinel/stay-area resets,
one per distinct same-area room, with the same global maximum of two to four.
Reject scripts, specials, fear/confusion/noncorporeality, randomized reset
rooms, unknown equipment/objects, weapons, and spell items. The capacity-only
rejection remains recorded. Post-loss no-reserve admission must independently
pass the existing incoming peak, observed defense, output, route, and exact
policy-loss checks. Audited route-program admission receives the bounded
capacity-endpoint flag only from this source proof; it retains its own route
hazard preflight. The live executor still requires one exact isolated useful-XP
target before combat, with the ordinary finite search and action budgets.
For this audited passive population only, the first live `Do you feel lucky,
punk?` result may enter the +2..+5 level band while the visit remains marked
capacity research. It still requires fresh same-room isolation, target identity,
route, and consider checks, and uses the 20% own-health withdrawal floor for
an unarmed target with no special. The separate HP comparison is report-only;
a sibling room's higher-level consider cannot override this target's reply.
When that capacity route is explicitly marked `no_combat_probe`, the endpoint
and every unregistered attacker remain observation-only, but one exact,
source-registered VNUM for an unarmed current-band transit mobile may use the
existing bounded transit-fight state machine to reach the endpoint. Isolated
instances of that VNUM may be fought up to the finite source-audited
reset-family cap, currently three for the largest registered route. This is
not a one-shot receipt, reboot-scoped quota, or permission to fight a crowd.
It does not admit the capacity endpoint itself, armed or special transit
mobiles, or XP credit for the transit kills; live identity, isolation,
consider, health, and return gates still apply.
That source-proved plain population may retain a nominally current-level
candidate whose source load fuzz reaches plus two only when the existing
post-loss no-reserve peak/defense/output proof passes. It does not raise the
live plus-one ceiling or bypass observed below-band, movement, kills, routes,
or saved failures. Source-less and all other capacity research keep plus one.
`plain_bounded_mobile_population` shares the complete prototype/reset audit
with candidate admission. For its wandering, ordinary XP targets only,
`_below_band_population_locator_allowed` may finish the current registered
search after a weak individual is rejected. Require exact source/policy/room,
awake noncombat state, known sufficient vitals, food/water, an isolated target
contract, and unchanged finite locator/kill limits. Exclude required-item,
quest, sanctuary/familiar, armed and special probes; ordinary harmless drops
are not required-item objectives. Preserve the negative consider and sightings,
and skip same-mobile rooms already queried in this visit. Each new target still
needs its own live audit; exhausted routes close without a same-room recheck.
An empty stop following the weak member retains this search context only when
its inspection is complete, it is explicitly skipped as absent, and the visit
contains an exact source/policy weak-member receipt. Seeded historical skip
names alone do not qualify. Keep crowd, mismatch, unattackable, loss, vitals,
and locator-limit stops authoritative. Run 16656 exposed this premature return;
its corrected handoff is not yet live-proved and grants no new campaign retry.
Reconstructing run 16648's observations with current source selected the
remaining registered 16471-to-16479 route on refresh eight. This is offline
evidence only; no historical result, saved exclusion, or live kill was changed.
New cases compile and await October 11.

For the same source-proved plain population, a useful objective kill may start
the first post-kill `where` query after an outbound interception skipped the
initial locator. Ordinary harmless reset drops do not turn XP hunting into a
required-item objective. Existing damage-window/unprotected-HP-fuzz checks
remain attached to every fresh isolated target; lookup grants no attack
permission. Require exact policy/mobile kill identities, reward above the
current-level-times-ten below-band floor, latest positive consider, known
awake vitals, provisions, and no combat, loss, hard abort, or runtime return.
Continuation health uses the source upper-load peak round, one extra critical
hit, and the 20% withdrawal reserve, with the ordinary continuation minimum.
Carry that entry requirement to the relocated stop without changing its
separate combat withdrawal floor. Retain weak-instance receipts only when
each has an exact-policy source sighting; skip those rooms and all same-visit
checked destinations. A query needs no old positive locator, but its reply
must positively identify a registered, unsearched safe destination before
movement. Preserve the finite locator, population, and kill budgets. Required
loot, sanctuary/familiar objectives, protected/special probes, and historical
cooldown changes remain excluded. New replay cases compile but are unrun.

Ordinary XP routes have a separate economic-only admission in
`economic_hunts.py`. Require a passive, unarmed singleton sentinel target, an
otherwise eligible source route, and a known whole purse no larger than 1,250
copper-equivalent. Every economic actor must have either exactly one global
singleton reset, or an independently audited two-to-four-reset, same-area
singleton population with identical reset counts from 1-4. It must have only
`spec_thief`, no aggression or programs, and an audited ordinary loadout
without spells, poison, positive damage bonuses or unsafe randomisers.
Its upper source level cannot exceed the player. DD4 steals 1-20% per attempt;
250 is the maximum single attempt at this purse ceiling, not an aggregate loss
cap. Retain the original economic rejection and actor identities in the saved
candidate. Recheck source and current money before outbound actions; failure
returns home. This authorizes no combat with the thief, crowd exception, saved
failure retry or quest waiver. Existing live isolation, route, consider,
training, health/output, finite-action and return checks still apply. Mirror
Realm buck/moose source candidates pass this narrower admission. Run 16658
proved the buck kill for 2,084 XP without sanctuary, a 50.6% lowest observed HP,
and safe healer return. The moose failed live consider, so the full two-target
objective remains not-achieved. The next visit's finite city waits failed to
clear the route; retain that block. New regression cases await October 11.

The economic-only allowance may also accompany an independently source-proved
plain population of two to four distinct, same-area resets. Remove only the
economic rejection; retain `status=reject` and the capacity-only rejection so
the existing isolation research, damage, output, loss and finite-search gates
remain authoritative. Audit every target reset's objects. The bounded route-
program preflight may accept only the explicitly audited economic actors, and
noncombat locator paths receive their exact VNUMs through the existing source
economic-transit audit. Unknown, armed or changed locator actors remain closed.
The multi-reset economic form above is transit-only: it bounds reachable
noncombat thieves and never turns them into targets or waives a target's
isolation, output, consider, or loss gates.
The live purse cap still applies before outbound actions, including after gold
loot. Quake's four level-30 Westreen citizen resets pass source preparation
without sanctuary. Run 16664 followed positive sightings, but source identity
remained ambiguous: 12041 and 12042 have the same room description and reachable
rooms, with different source levels. It returned without combat, XP or loss;
success/not-achieved/safe. Preserve that failure, not an absence claim. Do not
infer a prototype from its instance selector or reuse an identical-profile
alias for differently leveled mobiles. New cases compile and await October 11.

`target_inspection.py` resolves a distinct contract: DD4's `look #<instance>`
prints the source mobile's full description before its health line. The parser
now retains that description. A passive, isolated ambiguous target may receive
one exact-instance look with a five-second deadline, at most eight per run.
Require all reachable prototypes to be known, passive, unprogrammed and without
specials, plus a unique complete expected description. Match the description
and named health acknowledgement, not gender guesses or substring keywords.
Keep the receipt under the travel controller, bound to instance, room, stop,
level, boot and source descriptions. It expires after twenty seconds; movement
invalidates it. A known different prototype skips the stop without attacking.
Unknown, partial, expired or changed output cannot authorize combat. Continue
with fresh consider, isolation, equipment, health/output and finite-action gates;
GMCP's post-opener VNUM must still match the intended prototype.

The exact old ambiguity-only visit may receive one
`campaign_target_inspection_revalidation`: require its linked completed run
summary with no combat/kills, unchanged level/boot/source/XP/loss and healthy
healer boundaries, the same candidate/route, and a currently distinguishable
description set covering the recorded source identities. Keep the old result
inside the receipt and in the research ledger. Consume before dispatch; the
new failure remains closed. This never clears crowd, negative consider, loss
or another route failure. Saved replay cases compile but await October 11.
The exact first-generation article-prefix mismatch may receive one revision-2
parser check only from its own completed no-combat segment and bounded
512-event tail. Require the attempted revision-1 receipt, unchanged boundaries,
one dispatched exact-instance look, and a complete source-matching reply within
five seconds before the next command. Preserve `prompt_repair_of` and the
matched response event ID. The matcher now uses the full source short name,
not an article-stripped target alias. Recheck the current instance, source,
consider and all combat gates; revision-2 failures remain closed. Run 16665
proved the actual woman description but incorrectly rejected that reply; it
returned without combat, XP or loss. Its objective remains not-achieved.

Run 16666 freshly identified citizen instance #6752 using the corrected
description matcher, then passed consider and confirmed source VNUM 12041
through combat GMCP. It killed the live level-31 citizen for 2,641 XP without
sanctuary, flee or XP loss, reached a lowest observed 32.3% HP, and returned
fully recovered to healer 3054. Preserve the attempted revision-2 receipt;
this kill does not grant more parser retries or waive another policy's route
gate. Its independent level-100 objective remains not-achieved. Run 16668's
subsequent city-preflight stop was no target attempt and gained no XP.

An admitted temporary-crowd reset must not discard a source policy's confirmed
useful-kill result while leaving its weak-instance exclusions authoritative.
`productive_crowd_reset_result` retains positive evidence only for known same-
boot, positive-consider kills above the below-band reward floor, without fatal,
exhausted, retryable, route, absence or identity failures. Source loss policy
gates remain authoritative. Historical repair lives separately in
`campaign_migrations.restore_productive_population_after_crowd_reset`: require
an already-completed, unconsumed capacity wait, that exact cleared policy, a
source-proved plain population, current full healer state, the latest linked
success/success/safe visit in the existing tail, exact objective kills matching
the already-loaded normalized ledger, unchanged source/level/boot/XP/loss, and
a later successful same-state healer `time` visit. Preserve original outcomes,
weak-instance receipts and the two run IDs. Existing results, new losses or
failures, changed revisions, exhausted waits, and unknown evidence never reopen.
Checkpoint 49664 restored 16652 via time run 16653; ordinary selection admitted
the route. Run 16654's fresh city failure remains closed. New cases compile but
await October 11; no multi-kill live proof is claimed.

When ordinary current-band selection finds nothing, the separate
`campaign_population_search_revalidations` receipt may offer one exact saved
premature population return. Read only the already-loaded eight-segment tail
and its linked compact run summary. Require success/not-achieved/safe, no
combat/kills, unchanged level/boot/source/route/XP/loss, recovered healer
boundaries, one below-band individual, an unspent original eight-refresh
budget, and a live-reported, originally planned, current-source registered
room that was not checked. Keep the old negative ledger and locator evidence.
This is a retryable search, never fabricated productive history. Repeat the
ordinary source, route, output, survival and target-loss checks, then persist
the attempted receipt and segment ID before connecting. Any recorded receipt
closes another repair; fresh live identity, isolation and consider remain
required at every destination. This is not a general cooldown reset.

Equipment valuation uses `GearCatalog.observed_equipment_item` for exact
structured worn identities. Require matching integer VNUM, name, item type,
class compatibility, and an integer observed load level from 0 through 100.
Keep missing-slot/weapon-loss evidence authoritative. Substitute that level
only in a copied source item; bonuses remain source estimates. An ambiguous
carried description cannot borrow this worn identity. `show-gear-sources` and
campaign weapon-upgrade selection share the valuation; a lower-level placement
of the already-worn sword is not an upgrade.

Source hunt-stop preparation checks its own 60-second deadline before candidate
work and throughout destination/relocation loops. Expiry fails visibly before
connecting; it does not grant a target retry. `SourceRouteHazardIndex` belongs
to one unchanged `WorldSource` within that plan. Reuse reset groups, full-world
wanderer ranges, and level-specific special classifications, not route verdicts
or live observations. Discard it after the plan or any source mutation/refresh.
Stay-area navigation may search only the target area, while hazard checks still
use the full source graph and all source-known wanderers. Skipping an empty
combat-only hazard destination changes no permission. Keep the outer deadline
and every route, isolation, consider, output, loss, and live response gate.

`AdjacentRecallEscape`, owned by `RecoverySessionController`, handles one
source-known no-recall room with an open, unlocked, ordinary exit to a safe,
nonrandom land room. Audit source hazards/access and that area's default recall
to 3001. Reject Purgatory, water/air destinations, missing source, combat,
unknown posture, less than 50% HP, or less than ten movement. Verify the live
exit, then dispatch only scan, one movement, and recall. Each reply has a
five-second deadline and exact expected room; a complete immediate-occupancy
or closed-door scan stops the attempt. Distant sightings do not become adjacent
ones. Store `campaign_adjacent_recall_escape` on success and failure, and follow
the ordinary healer return afterward. This authorizes no combat or field logout.
Run 16640 proved the 16459 north 16465 recall 3001 escape after run 16639's
failed return. Its scan showed a clan member three rooms north, not adjacent.
The earlier failed run remains failed/not-achieved/safe despite its useful kill.

`campaign_recall_route_revalidation` binds one useful failed-return hunt to its
immediately following successful `return-home` segment. Load only the exact
policy's latest segment within 256 rows, its sequence neighbour, its compact
kill ledger, and its last eight events. Require unchanged level/boot/source,
an exact recall-only error, original source route, fresh positive consider,
useful objective-eligible kill, no original or recovery loss, and the recorded
three-command source-safe escape followed by healer recovery. Read the hunt's
own terminal state event: inherited campaign abort/consider flags are not that
run's evidence. A pending receipt changes selection only, never historical
execution/objective outcomes; consume it before opening the live segment.
Current crowd, below-band, source, output, movement, and target-loss gates still
apply. A later visit replaces the latest-policy evidence and cannot resurrect
the older receipt. The helper matches saved runs 16639/16640; automatic live
admission remains unproved. Cases in `test_recall_route_revalidation.py` are
compiled but unrun under October 10's spent regression allowance.

The Catacombs fallback stores Martin, Charles, Amanda, Sally, and Paul as separate
mobile objectives. Amanda (9512, reset 9510) and Sally (9514, reset 9514) are
source-confirmed level-30, unarmed, unprogrammed, same-area wanderers without
specials. Adding them does not expand the original three-target parent contract.
A parent-route cooldown from one linked, completed health-floor withdrawal may
leave an untried sibling eligible only when exact source-consider and presence
evidence identifies the failed mobile, with unchanged level, boot, source, and
accumulated losses and no death or route hazard. Preserve the parent result and
loss ledger. Each sibling keeps its own cooldown/loss record, exact source
route, fresh live identity/consider/output checks, and initial one-kill limit.
After another target fails, use that exact linked failure if it matches the
current accumulated-loss total; an older parent failure must not override it.
The exact extra-attacker/duplicated-GMCP abort may also scope its linked loss to
one source target. Require success/not-achieved/loss outcomes, a real combat
and XP-loss event, one useful consider/presence identity, no death or route
hazard, recovered full-health healer boundaries, and the exact current loss
total and segment-linked loss record. A historical positive research result
cannot override that newer loss. This negative scope survives a source refresh
only when the failed run's own start/end revision agrees; alternatives need
fresh current-source admission. Keep every same-level/boot child abort closed
across refreshes unless its separate recorded repair contract admits it.
Paul (9517, reset 9509) is level 30, unarmed, and has no special. Its one
`rand_prog` immediately breaks while fighting and otherwise executes one
`mpecho`. `mobile_programs.py` accepts only that exact five-line control flow,
a numeric chance from 0 through 100, and non-CHAT echo output. Other triggers,
actions, branches, or extra commands remain excluded. Source admission is not
live kill evidence and retains every ordinary hunt gate.
The proven idle-script shape retains ordinary three-step source-safe pursuit
even when a live health probe or protection check is required; those combat
checks remain unchanged. The non-aggressive unarmed no-reserve output gate may
use the same script proof; every source damage, output, reset, loss and live
check still applies. Aggressive or other scripted targets remain excluded.
After ordinary sibling selection finds nothing, one exact safe no-combat
one-step pursuit failure may receive `campaign_idle_pursuit_revalidations`.
Require a linked completed run, positive live locator and target presence,
unchanged level/boot/source/XP/loss, full-health healer start/end/current state,
no consider or combat evidence, and a newly proven three-step safe-room map.
Persist an attempted receipt with the prior run/segment before connecting.
Never clear the old route result, combat loss, or source policy ledger; any
failure or previously recorded receipt closes this one-use repair.
Receipts are sticky campaign metadata. If a terminal checkpoint lacks one,
restore only its exact consumed receipt from the already-loaded eight-segment
tail, with matching policy, level, boot and source. This recovery closes the
repair; it never copies gameplay state or creates new retry permission.
Cooldown ageing retains loss-bearing route results. If a legacy result is
missing, target scope may use that exact linked completed segment's terminal
result only for its recorded loss outcome and matching current loss ledger;
all level, boot, source, identity, and hazard checks still apply. A conflicting
current result takes precedence; never substitute history for it.
An expired parent cooldown never clears its recorded XP-loss fight. A child's
same-level/boot/source failed search remains closed from its exact bounded
segment evidence, including legacy attempts without a research-result entry.
Before-consider Catacombs aborts now record their own route failure and cooldown;
positive `where` presence is not proof of a reached target or a useful kill.
Relocation tables include safe positive-locator destinations beyond the eight
blind stops as origins. Every new origin retains path, hazard, access, and live
identity checks; blind stops and live relocation limits remain eight. This
repairs a missing map origin, not a consumed failed search or combat permission.
After one source-mapped room is rechecked and still lacks a source-ranked
wanderer, the locator may broaden to another non-empty source-mapped label only
when the locator explicitly permits continuation and the target/source VNUMs
match. The alternate leg is still source-routed and bounded by the same
eight-refresh limit; this never authorizes combat without fresh identity,
isolation, consider, output and recovery checks.
After ordinary sibling selection finds nothing, an already-productive exact
registered source identity may receive one `campaign_registered_locator_revalidations`
route check. Require its linked completed success/not-achieved/safe run,
zero combat and unchanged XP/loss within that run, full-health healer boundaries,
same level/boot/source, and the exact missing-origin abort. The final positive
locator must lack a registered origin, and the current audited map must provide
routes from that origin to every endpoint under its old reported labels.
Keep its prior locator decision and result in the receipt; do not clear either
the research result or target loss ledger. Later unrelated XP/loss remains
current and cannot substitute for evidence from this failed search. A recorded
loss for the exact registered or source target closes this allowance.
Selection saves a pending receipt; the segment start consumes and checkpoints
it before opening the connection. Fresh identity, isolated targeting, consider,
health, protection/output gates and the eight-search/refresh limits still apply.
Sticky attempted receipts forbid another automatic check after any outcome.
Run 16634 completed its fresh Martin objective for 1,923 net XP and retained
the attempted receipt at checkpoint 49605. Its ordinary repeat 16638 lost
189 net XP after Caroline joined. The old positive research result is historical
kill evidence, not permission to override the new registered loss. The consumed
locator repair never reopens that combat failure; checkpoint 49610 is recovered.
The higher-band Vampire Catacombs fallback audits each reset separately.
Anton (mobile 9501, level 35, room 9506) is a source candidate, but his current
combat stop requires Sanctuary, so source level and the short entrance route do
not make him an executable no-reserve target. His reset has no special or
program, wields the source-identified chef's knife (object 9506), and carries
the paintbrush wand (9504) loose; `fight.c` only zaps a wand held in
`WEAR_HOLD`, and the source audit rejects a loadout change that holds it.

The exact XP-loss receipt for Grok (9510) scopes that failure to Grok only.
The parent Catacombs failure and cumulative loss ledger remain intact. If a
source refresh makes that historical target scope unusable, the parent remains
closed rather than retrying an unknown mobile, but the independent missing-key
route remains eligible. At levels 38-39 the separate Joan key hunt (mobile
9506, room 9517) passes its source audit for the spiked key (object 9565), with
a 95-percent starting-health requirement and Peter retained as a checked
trivial bystander. The key opens the east door from room 9523; the bats, art
critic, and gallery visitors then pass their individual source audits. This is
candidate evidence only: confirmed key inventory, reachable live exits, exact
identity, consider, isolation, output, health, provisions, and return checks
still govern each attempt.

Joan's required-loot policy may fight an otherwise below-XP-band Joan when the
key is absent; that evidence must not close the key route as it would an
ordinary XP hunt. After a successful key hunt, the starter now enters the
reboot-scoped cache route from the healer before logout and verifies the key is
dropped in room 3007. The world-cache receipt is valid for the current MUD boot;
a later source-mirror refresh does not invalidate the physical cache, although
the recorded source revision remains useful provenance. The key is then
expected to remain available until the next MUD reboot; a missing cache receipt
still means the key was not preserved. Floor receipts remain source-checked.

The target-scoped loss and fallback behavior passed its focused campaign tests,
and all 120 `test_hunt_outcomes.py` tests passed on October 17. The full
regression suite was already run today and was not repeated for this change.

The default Midgaard recall shortlist is not the whole level-38 frontier.
From the registered Mirror Realm route's Suite (19170), source revision
9205f316 admits three close, plain level-39/40 opponents: the barkeeper
(19026, room 19071), the waiter (19027, room 19072), and Mr. Teece (19069,
room 19166). Each is a single-reset sentinel with no aggression, attack
program, combat special, or combat weapon reset; their exact source paths are
registered as one bounded three-kill visit. Each stop keeps the 20% health
floor, unprotected HP-fuzz probe, and live damage-window, identity, isolation,
and consider gates. No sanctuary is required if those gates pass. This is
source-approved opportunity, not live proof of presence or a kill. Positive
alignment on Teece may shift Dorrik's alignment further negative under
`xp_compute`; fame and XP remain separately observed.

An eligible target route may first use an existing affordable optional flight
purchase. Preserve current food/recovery, nonnegative fame, shop-route and
purchase cooldowns, purchase-failure evidence, fresh price/stock, and live
affect verification. An unaffordable or failed purchase never grants departure.
At healer 3054 before departure or after the registered field return, retain an already-applied combat loadout when
only movement is low and HP is at least 95% and mana at least 50%. Swapping
movement gear can change the maximum and otherwise oscillate loadouts. Keep
the ordinary movement ratio, absolute route budget, and recovery checks; this
does not lower departure readiness or replace HP/mana recovery gear.
The return case includes a movement-only pending recovery flag, but keeps the
registered healer return and ordinary sleep/readiness requirements. Damaged
or mana-depleted characters still use recovery gear.
October 10's single focused regression batch passed 26 tests. The later
cooldown-expiry, locator-origin, expanded-target, and optional-flight changes
and their extra cases are compiled but not pytest-verified;
do not run another regression batch before October 11 local time.
Run 16628 live-triggered the new 20% threshold against Sally. Flee took another
violence pulse and HP reached 48/702; the character returned to healer 3054 and
finished fully healed. Record execution success, objective not achieved, and
safety loss independently: 551 flee XP lost, 846 damage XP gained, +295 net.
The prior successful Sally kill never clears this new failed fight.
Hoard guardians are dynamic spawns: their player-derived level, HP, and extra
level/2 damroll replace the ordinary reset assumptions. The standalone guardian
calculation reports raw attack bounds, not complete damage after victim-specific
effects and not a proof that the dig lag and escape can be survived.

For passive-defense probes, `combat_defenses.py` mirrors `fight.c`'s sequential
shield-block, parry/pre-empt, and dodge rolls. Require
observed positive proficiency from the current level/boot training audit,
matching current skills, normal form, structured equipment/affects, and an
awake, unimpeded character. Ordinary probes remain limited to plain targets.
One prepared armed-target probe is permitted only for a fixed sentinel with
exactly one source-identified, reset-loaded ordinary weapon; reject specials,
programs, aggression, fear aura, extra resets, bows, and other combat gear.
Require at least 95% player HP, enough HP to survive one raw peak while
retaining the 22.5% reserve, a raw peak within 67% of maximum HP, a combined
normal-hit probability of at most 1/2, and source output covering the target's
maximum loaded HP plus expected incoming damage. Use the target's maximum
loaded level and strict percent-roll boundary; ignore armor misses, dual parry,
and other unproved mitigation. The probability reduces expected normal-hit
damage only; never discount the raw peak. Preserve the fixed action budget,
route preflight, live isolation/consider/damage window, and exact target-loss
closures. All other high-peak armed targets still require sanctuary or learned
disarm. Save `campaign_source_ranked_passive_defense_estimate` as source-only
evidence, not a retry marker or live authorization. This never reopens a
recorded loss or any below-band/route exclusion. Focused tests were added for
the October 8 change and await the next daily regression window.
Save `campaign_source_ranked_passive_defense_estimate` as source-only evidence,
not a retry marker or a successful combat observation. This never reopens the
bard's recorded loss or any below-band/route exclusion. October 7 compilation
passed; the new focused cases await the October 8 daily test window.

An improved-output revalidation may retain one exact low-level route-program
hazard only when `_source_ranked_route_program_candidate_allowed` validates the
candidate's registered `where` preflight. This is not a route-hazard bypass:
issue the locator fresh before crossing and return if it finds the mobile. The
existing one-shot loss marker and all post-loss output, health, identity, and
consider gates remain in force.

For a source-ranked route that crosses a plain wandering aggressor, a positive
`where` result anywhere in the current area closes the no-combat transit proof,
even when the reported room is not on the planned path. The mobile may move
between the origin locator and an adjacent scan; generated routes therefore
recall on any positive location and retain their bounded scan checks for a
negative result. This protects route identity without reopening the failed
target or authorizing combat with the wandering mobile.

For the exact policy with the prior damage-window loss, admit the post-loss
plain-target variant only when that one-shot revalidation proves a strictly
higher source output ceiling covers the observed target HP. Its independent
incoming-damage bounds still apply; this does not reopen a second attempt.

Persist consumption on the exact loss record and loss event, not only in the
single active marker: selecting a different target must not make the earlier
attempt available again. Startup may repair a legacy record only from a
matching source-ranked segment whose marker, policy, target identity, observed
HP, output ceiling, and loss event agree. After selection consumes the marker,
the active stop builder may carry that exact proof through only when the same
policy, level, boot, target, source revision, and current output signature
still match. This preserves the selected probe's no-sanctuary admission; it
does not reopen selection, grant a retry after interruption, or relax any live
consider, isolation, health, route, damage-window, or return gate. A verified
objective kill clears that policy's loss record, allowing future evidence to
be evaluated afresh.

Prefer current-band fights with the best expected net XP per whole-session
time when the observed gear, trained skills, and source-backed output support
the existing finite combat budget. Do not require sanctuary just to avoid
ordinary damage when the exact plain-target no-reserve rules pass. Keep live
`consider`, target identity, useful-XP, incoming-damage, and survival checks as
hard gates; increased aggression means using proven capability, not weakening
those checks.

After a same-level XP loss, the plain-target HP-fuzz probe may use a combined
source exposure ceiling of 65% of maximum HP: the worst source round plus the
extra damage from one critical hit (half the doubled critical total). This is
30% above the former 50% post-loss ceiling, but remains below the ordinary
80% unprotected-probe ceiling. Require an exact fixed sentinel with one reset,
no aggression, fear aura, program, special, or wielded weapon; retain the
source-output lower-bound and HP-uncertainty checks, route-program `where`
preflight, and all live isolation, `consider`, damage-window, and return gates.
The 50% limits for route-loss and partial-timeout retries are unchanged.

For a passive post-loss target whose source-loaded level range straddles the
five-level useful-XP floor, use the range's upper bound for bounded-probe
admission; the nominal source level alone must not close it. This is only
permission to run the exact route preflight and fresh live `consider`. The live
result remains authoritative: a result at -5 or lower closes that reset before
combat and cannot earn progression XP.

The passive contract above remains unchanged. A separate aggressive post-loss
probe may be armed once per level and reboot only for one exact, fixed,
unarmed sentinel with one reset, no special, program, fear aura, or confusion.
Require the source-loaded minimum level to be strictly greater than
`character_level - 5`, the maximum no more than `character_level + 2`, the same
65% peak-plus-critical ceiling, and source output covering the lower HP bound
and uncertainty gap. Persist the exact target marker and consume it before the
segment opens. Start at 95% health; fresh route checks, isolated live identity,
useful `consider`, observed damage window, and bounded withdrawal remain
mandatory. A second aggressive probe at that level and reboot is closed even
after interruption.

Live result from run **16569**: Dorrik's exact source-ranked Olympus policy for
Samuel the Armourer (mobile 918, room 935) reached the live fight, then withdrew
at the hard-health floor before an objective kill. The source output ceiling was
1,392 against 792 observed target HP, yet the segment recorded 551 XP lost
(level 30, boot `Sun Sep 27 23:55:43 2026`). The checkpoint stores this exact
policy in the current-boot XP-loss ledger; do not retry Samuel or infer that the
source output estimate proves the exchange survivable. Select a distinct
current-band policy and retain all ordinary live damage and withdrawal gates.

Reject a passive armed combat-special HP-fuzz probe during source selection
when the runner cannot open it without enemy GMCP HP. DD4 `update.c` sends that
HP only during combat; `consider` does not supply it. Preserve the existing
source-audited economic-special exception and every ordinary opener gate.
Run 16453 demonstrated this unsupported armed cleric shape at Solace's
Lieutenant Commander: exact consider succeeded, but no opener or potion was
dispatched. Do not make pre-combat enemy data appear by weakening the runner.

Keep a selected affordable flight purchase ahead of protection-frontier
rewrites only at a provisioned, recovered healer checkpoint with observed
nonnegative fame, zero next-level QP shortfall, and no active shop-route or
purchase cooldown. The ordinary runner must still verify its source route,
current quote, stock, purchase, and resulting flight affect. An empty XP
frontier may select already-audited ground-stash or coin-carrier funding under
their existing admission and retry contracts; record it as maintenance, not XP.
Treat a fresh fly/levitation affect as sufficient only when its known duration
meets the selected route's source-derived reserve; a generic flight objective
requires positive duration. If an active affect is too short, stay at the
healer, handle observed food or thirst needs, and sleep on the same connected
session until it expires before buying and verifying one replacement. Duration
zero is not route-ready flight, and repeated save/quit shop probes do not age it
productively.

`scan` describes each sighting's distance. The pre-entry check concerns the
immediate destination, so only an exact target **one** room away in the chosen
direction blocks that step. A sighting three rooms down the same direction is
not evidence that the adjacent room is occupied. Preserve the whole-route
`where` preflight and fresh checks before later registered destinations. This
parser correction does not reopen historical failures or spend new retries.

Hex inventory planning uses current effective STR/DEX minus level/4, floored
at three. Hidden over-cap stat surplus can only improve that lower bound.
Capacity changes affect pickup; `move_char` and `get_move_ws` do not forbid
walking solely because weight or item count exceeds the new capacity. Preserve
already-carried belongings. Separately check `affect_modify`'s primary-else-dual
weapon drop against the new STR wield limit. Use the existing exact required-
loot capacity relief for pickup, not an invented post-hex disposal loop.

Equipment removal text arrives before `Char.Worn`. Capture a removed item's
unique already-observed source identity before clearing its slot; otherwise
the later diff cannot recover it. Keep hints session-local and require current
inventory presence. A known nonweapon removal is not primary-weapon loss;
unknown removals remain conservative. A single role-compatible primary stays
equipped during recovery unless the full proposed loadout improves the existing
HP/mana/stat priorities, including set bonuses. A hitroll-only change is not a
reason to replace it while sleeping. Combat/pre-level ranking remains unchanged.

Recovery identity revision 2 permits one fresh comparison after an exactly
matching legacy five-command verified restoration. Both saved plans must match
the current source/inventory plan, level, and reboot. Persist consumption and
the old result in `recovery_identity_repair_of`; never reuse an old comparison
reply as current item identity. Repaired or changed results stay closed.
One separate response-parser revision-2 check may follow only the exact legacy
three-command `weapon comparison timed out during compare` failure. Preserve
that failure in `prompt_repair_of` and preserve an already-consumed restoration
marker. Split complete prompts before matching period-terminated reply lines;
asynchronous healer chatter can precede a valid reply without a newline. Five-
second deadlines, fresh equipment/inventory, exact comparison, and post-wield
verification still apply. Neither repair clears any combat loss or hunt closure.
Persist comparison audits on failed runner exits as well as successful ones.
A legacy dispatched-only record may recover the missing failure audit from its
matching failed comparison in the existing segment tail: unchanged level/boot,
identical start/end request, healer endpoints, unchanged visit XP/loss, the exact
compare-timeout terminal error, and only the three read-only comparison decisions.
Require the entire visit to fit below 128 stored events. Preserve its run ID and
all current loss evidence; missing, modern, changed, or post-wield records remain
closed. This recovers a result, not a comparison reply or permission to hunt.

Before any opener, a source-resolved guard bystander must pass the target-aware
alignment/non-hostility check even below the ordinary assistance-level window.
Keep it in the room-hazard set until then, ahead of trivial-bystander and cached
non-assisting shortcuts. Run 15984 lost 576 XP after a level-15 townguard joined
the level-29 player's fight. Preserve that loss and its closed policy; this fix
does not authorize a retry. Telnet `update.c` serializes the primary enemy for
each participating room combatant, including possible allies; duplicated rows
prove neither identical prototypes nor a harmless duplicate. Do not deduplicate
them or substitute the repeated primary level for another attacker's level.

Startup equipment reconstruction uses the ordered live primary-slot replay.
Do not set `campaign_has_weapon` from absence of a loss message or by looking
up shared worn names. A failed connection that issued zero commands and matches
the pre-login transport classifier can be skipped using only the loaded segment
tail. Stop at the next real run, including a disarm, an empty slot, or a partial
post-login failure. This repairs transport-only checkpoints without reviving
equipment after actual loss or broadening history scans. Report connection
establishment failures separately from failures to reach a usable login.

A healthy pending lesson at the exact source-registered distant class teacher
does not need the later XP route's movement pool. This applies only after the
training trip has started, with no return/abort/runtime boundary, no combat,
known positive vitals, at least 95% HP, 50% mana, eight movement, no active food
or water need, and no poison or blindness. Preserve source teacher identity and
all existing practice checks. The separately registered consumable-invisibility
journey keeps its own rules. Once training completes, ordinary healer return,
movement recovery, and combat readiness apply again. Never apply this lesson
exception to a route waypoint, merely similar room name, or hunt target.

The one-shot long city-route revalidation uses the same productive-repeat
admission as ordinary source selection. Its fresh-candidate three-kill cap
must not discard a route independently admitted by same-boot meaningful XP
evidence. Compute that admission over all ranked candidates, including those
with the exact city-only block, and record `repeat_after_kill_cap`. Retain the
unchanged no-travel blocked segment, later run-matched unblocked locator,
source/level/boot identity, 22-extra-command ceiling, and consumed retry marker.
Every ordinary selection, source and live combat gate still applies; this is
not a second attempt after an already-consumed route revalidation.
Run 15974 live-proved selection after that repair, then stopped on fresh Poor
Alley hazard sightings. Its clear city-prefix record is not contradictory:
the separate full-route check covers later city rooms after the sewer section.
The consumed marker stays closed; do not reinterpret that result as a stale
abort or use the partial prefix to authorize the remainder of the path.

Connected quest waits must continue reading the socket between thirty-second
`quest time` queries. Do not sleep the reader for that interval: queued healer
chatter can strand fresher GMCP and create a false no-progress result. Treat the
exact `quest time` cooldown replies and DD4's `You may now quest again.` message
as live quest-status updates even while duplicate-login filtering suppresses
later `Char.Quest` snapshots. Keep resource maintenance, the 180-second
no-progress stop, and the finite segment deadline. DD4 calls `quest_update` on
the randomized area pulse (30-90 seconds), not on an exact one-minute schedule.
One legacy sleep-before-read stall may reopen only from its exact single
cooldown phase at the recovered healer, unchanged level/reboot/XP/timer,
nonnegative fame, and a required next-level QP shortfall. Persist reader
revision 3 and the old marker before dispatch; a repaired-reader failure cannot
reopen this legacy exception. When a fresh status reports no active quest and a
zero timer, request again immediately on the connected quest phase; do not
impose a level, reboot, or campaign-history quota.

A loose-item quest may cross source-audited `spec_thief` mobiles with a known
whole ordinary purse of at most 250 copper-equivalent. Audit every reachable
pickpocket as passive, unarmed by reset, unprogrammed, without fear aura, and
with no other special. Retain all other route hazards, source access, program,
movement, and live safety gates. Limit the recall-origin path to 60 commands
and exclude randomized exits. Persist the exact giver/room/object identity and
mobile VNUMs on the route; recheck the active loose retrieval, purse, and source
profile during outbound travel. No combat target is authorized. The cap covers
the entire purse, not just one 20-percent theft; DD4 only steals copper, silver,
gold, and platinum through `total_coins_char`. Source analysis of the rejected
run-15955 Yggdrasil assignment passes a 36-command route to object 76 with
pickpocket 9911; that abandoned quest is not live completion evidence.

Source-required next-level quest points and optional frontier requests are
different objectives. First try executable current-band XP during a positive
quest timer. If none remains, a recovered, fed healer checkpoint with observed
nonnegative fame and a source-defined QP shortfall may select `quest-cooldown`.
Reuse the existing connected wait, finite runtime, food/water maintenance,
fresh assignment and source route checks. DD4 advances `nextquest` only while
the character is connected. If the worker cap arrives first, finish safely at
the healer and resume the same campaign promptly; do not wait offline or treat
the positive timer as a failed request. Keep each worker bounded and preserve
the live timer as the only request cadence gate. An unchanged timer closes the
next wait. A same-level/boot dispatched request plus ordered live phases
showing cooldown zero and then a positive active quest identity proves that a
later cooldown is new, not stalled. Remove that phase evidence when the next
wait is persisted, and persist completion as an explicit null wait marker so
ordinary maintenance cannot restore the older timer. Legacy checkpoints may
recover this fact from the latest quest wait in the existing bounded segment
tail only: require success, a run ID, identical saved wait marker, matching
level/reboot, and the ordered positive assignment evidence. A later quest
segment or changed marker closes this repair; never expand the history scan.
Never infer a new cycle from selection alone or an unacknowledged request.
There is no campaign request limit by character level or reboot. Require a
complete observed quest status with valid `active` and `nextquest` fields; a
missing or malformed status is unknown, never an expired timer. The active
assignment and timer are the cadence gates: request only when inactive and the
timer is zero, and allow another request after DD4's timer expires. Campaign
request markers are audit history, not eligibility gates. A
source-required quest request for a remaining next-level QP shortfall remains
available after executable current-band hunts are exhausted and the healer,
food, water, fame, and live-quest gates pass. A selected cooldown may dispatch
after the observed timer reaches zero; do not require an unused campaign marker.
Do not defer that dispatch solely because less than 180 seconds remain in the
bounded session; the inactive status and zero timer are the cadence gates.
A direct `quest-request` can establish the same new-cycle fact when its saved
start explicitly has inactive quest status and zero cooldown at the same level
and reboot, followed by a dispatched request and positive live assignment.
Legacy repair may read that start alongside the end in the existing bounded
tail, but its first recorded quest phase must match the segment. Missing
availability, a changed reboot/level, or an unaccepted request cannot clear a
wait marker. Run 15955 exposed this direct-request case. Checkpoint 48490
confirmed the legacy marker repair, and run 15958 selected the connected wait;
this is maintenance evidence, not a completed quest.
New-cycle evidence requires an explicitly positive observed `active` flag.
The legacy snapshot parser's inferred activity from object/mobile fields is
not enough: stale identities must not override inactive or missing status.

Quest handoffs share a socket, so preserve the preceding policy's current
structured worn items, primary identity, instance mappings, ranged/chain facts,
and removed-item hints. Copy containers rather than aliasing them. Keep weapon
loss/refusal evidence independently, including when structured gear is stale.
Do not copy pending commands, completed gear audits, or route cursors. The next
text audit remains mandatory but must not overwrite a current structured identity.
DD4 `update.c:4415` only sends changed `Char.Worn` data: requesting `eq all`
cannot be relied on to resend it. Run 15951 lost that identity at the cooldown
handoff and replaced branch 6104 with club 1521. The handoff fix compiles; its
new positive/stale/loss regression cases await the next daily test batch.

Old research-rotation exclusions must not turn an already-affordable flight
purchase into another funding hunt. The narrow maintenance admission requires
food, affordability, no flight, no current purchase failure, and no observed
reputation refusal. The caller's route cooldown still applies, and the live
shop listing must confirm price and availability before buying. Run 15950
proved the repair: 345 copper-equivalent covered the freshly quoted 141-copper
potion, leaving 204 and a positive fly affect. It earned no XP.
When food is missing and city restocking is affordable, choose it before an
emergency equipment sale, including while already flying. Normal sellable-loot
liquidation keeps its independent priority and item-protection checks.
Run 15952 proved this combined ordering: six pies purchased for 174 copper
while already flying, with 30 copper-equivalent left. No emergency gear sale
was required. All new focused regression cases remain unrun on October 2.

The source contains three `a long, grey branch` prototypes: light 6103, weapon
6104, and trash 6105. Names alone cannot prove their weapon role. Resolve a
current structured primary through exact VNUM, item type, source description,
and class compatibility, retaining reconciled weapon-loss and empty-slot
evidence. Use that same identity in ground/carrier upgrade ranking, not the
lowest-VNUM same-name object. Contradictory structured identity must not fall
back to its worn name. Legacy unique names and separately carried role weapons
retain their existing checks; this does not identify an ambiguous carried item.
Runs 15941/15942 repeatedly saved and quit because campaign role matching chose
the light while the live executor correctly saw the weapon. The corrected
selection moved on in 15943. Run 15946 then proved the carried-branch recovery:
checkpoint 48447 has weapon 6104 equipped instead of club 1521, with full health
and unchanged XP.

`compare-carried-weapon` is noncombat healer maintenance, once per level and
reboot, recorded in `campaign_carried_weapon_comparison` before dispatch.
Refresh `eq all` and inventory; require one equipped weapon, one carried
candidate, exact text/GMCP inventory counts, and source mappings for every
carried item. The shared name must contain exactly one usable, releasable weapon
prototype, with a command keyword shared by its variants but by no other
carried prototype. `compare <keyword>` omits the second argument deliberately:
DD4 searches worn gear only when that argument is absent. Only the exact
better-than reply against the known primary permits `wield`; fresh `eq all`
must then confirm the expected VNUM, type, and name. Each reply has a five-second
deadline. An unclear, worse, incompatible, or changed result closes the attempt,
not a retry loop. This type-resolution contract grants no combat permission.

If an earlier successful comparison's exact reference weapon becomes primary
again, one healer-side restoration check may repeat the full comparison at
the same level and reboot. Require the earlier five-command verified result
without failure and the same current source plan (candidate, reference, names,
and unique keyword). Preserve it in `restoration_of` before dispatch; that
field closes any second restoration, even if the new attempt fails. Fresh
equipment and inventory, a new exact better-than reply, and post-wield VNUM
verification are still required. Never infer that a same-named carried item
is the same instance across reconnects. This repairs an observed equipment
reversal without clearing hunt failures or granting combat permission.
If the same source-resolved carried candidate remains available but the worn
primary VNUM has changed since a verified comparison, allow one further check
at the same level and reboot. Require the exact prior five-command success and
unchanged candidate VNUM, name, and unique keyword; save the prior primary
identity as `primary_change_revalidation_of` before dispatch. This allowance
is consumed once even if the primary changes again. Repeat every fresh
equipment, inventory, comparison, and post-wield check; a failed or ambiguous
result does not reopen it, and it grants no combat permission.

Run 15968 live-proved the restoration, and checkpoint 48510 after two further
wait segments still records weapon 6104 equipped. The October 3 focused batch
exposed incorrect wear flags in the synthetic comparison fixture; they are
corrected, but the correction has not been rerun under the daily test limit.

For pounding-weapon rearm, an absent `list mace` at Dave the Dealer allows one
live `where dave` check. Parse the complete source short description before the
room label, then map that exact label to at most four source-reachable Midgaard
rooms. Prevalidate one source-safe circuit through those rooms and back to
healer 3054, capped at 22 commands total, with enough observed movement for
the remaining circuit at every stop. Reject private or solitary route rooms.
Dispatch each leg only from its recorded origin; if that origin changes,
return to the healer and close the attempt. Issue one fresh `list mace` at each
candidate room, buying only after a live listing proves the shop is present.
After one circuit, return to the healer; never repeat `where`, guess a room, or
turn locator navigation into combat permission.
If that exact route ends safely at the healer with unchanged level, boot, source
revision, XP, loss totals, and wielded primary, persist the failed optional
rearm attempt and continue with another eligible current-band policy. An empty
single live locator check is also a completed optional attempt, not permission
to repeat the shop journey. Require a linked run and nonzero commands. Retain
the proof XP/loss totals in the marker; later XP gains do not reopen this route.
The marker expires when level, boot, source revision, or primary weapon changes.
It never overrides a missing-primary or required-piercing-weapon gate, and it
does not authorize using `stun` without a confirmed pounding weapon.
One route-code correction may reopen only the exact safe marker whose linked
failed segment records Dave's room label as having no bounded
source-reachable room set. Require the same level, boot, source revision,
primary weapon, healer checkpoint, and the linked segment's unchanged XP/loss
and safe-return evidence. Consume the correction in the original marker and
checkpoint it before opening the segment; it cannot be repeated. During the
registered outbound route, a complete current room listing may instead identify
Dave at an exact source-reachable room VNUM on that route. Stop there only when
the source shopkeeper identity matches, the registered route prefix and its
reverse still match open source exits, private/solitary rooms are absent, and
observed movement covers the return. This uses exact live room identity, never
the ambiguous `where` label, and grants no combat permission.
For a Thief/Bounty Hunter stun opener, only the positive collapse message
authorizes the follow-up backstab. A missed attempt can start combat through
DD4's zero-damage path, and `do_backstab` rejects an already-fighting target;
restore the primary weapon and use ordinary combat instead. Keep the existing
source, target, and survival gates unchanged.

Source `do_kill` adds no `WAIT_STATE` when it replies exactly `You do the best
you can!` to an already-fighting player. Release that command window without
adding another combat-round delay, including when a preceding automatic parry
acknowledged it first. Keep the reply request-local and bounded; quoted speech,
other commands, and normal damage replies do not inherit this exception.
Between-round action cooldowns, damage probes, and survival gates remain active.
For current ordinary progression runs, allow 300 seconds per segment: the older
180-second cap forced run 15929 out of combat after only 16 seconds. This is a
finite whole-segment allowance, not permission to extend any combat action limit.

DD4 `gmcp_update_quest` labels both loose objects and buried hoards `retrieve`.
Preserve that wire type. Only a real dispatched `quest request` opens the
five-second, 4,096-character narrative window. Match the exact questmaster's
hoard announcement to GMCP giver, room name, and area, then bind its annotation
to positive giver/room/object VNUMs. Retain it for that active identity only;
reconnect, a new request, inactive status, or changed identity clears it.
Unsolicited text and item names cannot authorize digging. The hoard generator
has a 5% chance to arm a trap with up to three charges, including curse, hex,
and a spirit guardian. Each triggered charge makes `do_dig` return before
contents spill; exhausting the charges can require up to three more digs than
the depth estimate. Known hoards currently abort with an explicit trap-handling
blocker; the former fixed twelve-dig sequence is removed. The standalone
controller now budgets those extra commands and pauses for an explicit, freshly
verified trap recovery before another dig, but live dispatch does not provide
that recovery verification or the physical return yet. Do not treat the
controller change as permission to dig. Ordinary loose retrievals keep the
existing source route and exact-object checks.
On October 4, Dorrik purchased the source-identified Midgaard Grocer spade
VNUM 3393 for a live quote of 70 copper (run 16162) and returned to healer room
3054. This is a valid `ITEM_DIGGER`, and the campaign recognizes it as
satisfying the tool capability check; its lower throughput means more digs and
tighter movement planning, not a requirement to buy a better shovel. The quote
is boot-specific, so list the item before buying. His quest request is already
used and no hoard is active; do not repeat the request. For former Forest room
18022, the spade's source values `(36, 3, 9, 160)` estimate 15 minimum-damage
digs plus up to three trap-charge digs: 18 commands and up to 3,654 movement
before return in the conservative total budget. The controller budgets one dig
at a time and can pause for movement recovery, but live trap handling and
physical return remain unintegrated. Its checkpoint API resumes only from a
safe boundary with a newer observation; an interrupted dig awaiting its reply
stops until ordered events are reconciled. Matching checkpoints now pass
through the quest-session owner and campaign state, but no live dig is attached
to dispatch. The parser also keeps a compact room-render snapshot after the
exits, visible listing, and prompt arrive, and clears it on a room transition.
DD4 `act_info.c` uses the same runtime `target_id` prefix for objects and
mobiles; these raw lines are not prototype VNUMs or proof that the room has no
hidden occupants. They are not yet consumed by a live digging gate.
The strict source
return check admits no unconditional path from that room to a healing-flag
room. `hoard_return_plan(...,
allow_exact_live_where_hazards=True)` now recognizes only the audited cityguard
and drunk profiles, records their VNUMs as mandatory live `where` checks, and
builds conditional outbound and return routes. The exact `where` selectors are
`cityguard` and `drunk`. `live_escape_issue` must clear the outbound path and
every random flee/return branch before digging; `live_route_issue` must be
repeated with fresh complete locations before each route leg. The planner now
also accepts an explicit `flying=True` estimate: DD4 divides eligible travel
movement by three while flying, but this does not reduce tool movement for
`dig`. A flying route plan is rejected by its live route/escape checks unless
the flight affect is freshly observed for that leg. Refresh or verify flight
before each leg; never assume it will last through excavation. Walking remains
the default and worst-case estimate. The unflown Forest route is 40 commands
each way; it estimates 221 movement outbound and reserves 231 movement for
return and flee. Its north flee branch re-enters the hoard room and requires a
fresh check that guardian VNUM 83 is absent from the remaining route. This is
planner evidence only, not live dispatch or permission to ignore an occupied
route. `build_source_hoard_execution_plan` passes its configured route limit
(no more than 240 commands) into the outbound/return planner; movement circuits
still enforce the total command budget. This does not admit randomized exits
or source-hazard rooms. `HoardDigSession` now pauses for movement recovery,
preserves its return reserve, and records a uniquely identified trap effect
from DD4's response; unknown or mixed effects stop the session. It still does
not resolve trap effects, fight guardians, issue sleep/wake, or prove recovery
safe. Keep live digging disabled until an integrated,
source/live-gated recovery cycle and physical return are implemented and
replay-verified. See
`docs/QUEST_HOARD_AUDIT_2026-10-03.md` for the assumptions and run evidence.
Questmaster routes are registered from recall room 3001. When a live checkpoint
starts at the healer in room 3054, prepend the source-verified `south` step and
set 3054 as the route origin; keep 3001 unchanged and reject other origins
instead of replaying recall directions from the wrong room.
DD4 kill quests retain an exact mobile prototype VNUM. `fight.c` marks the
quest kill complete on that VNUM without checking the hinted room, so the
campaign may choose another source-listed reset for the same prototype only
when the normal source admission succeeds. The assignment room remains search
evidence; alternate resets do not relax route, live identity, isolation,
consider, output, or recovery gates. Do not apply this rule to object quests.
The October 3 source audit is in `docs/QUEST_HOARD_AUDIT_2026-10-03.md`, including
double-fuzzed tool costs, terrain/stat modifiers, first-trap abort, invisibility
loss, cursed physical return, and the guardian's partially overridden prototype.
The standalone `excavation.py` controller and tool budget are implemented but
not enabled. `QuestSessionController` can restore and persist a checkpoint
only for the same narrative-verified active hoard assignment; a malformed or
changed-identity checkpoint is recorded and cleared. The Telnet reader now
forwards response chunks to an already active session only while its exact
assignment still matches; changing or clearing the quest drops that controller.
The owner can start a dig controller only after that exact assignment is
observed on the current connection; repeated setup cannot reset an active
controller. Polling, trap-recovery confirmation, and pickup use the same
identity gate. This connects observation and construction only, not permission
to dig. `StarterBotRunner` does not call those adapter methods yet, and the live
campaign still does not construct or dispatch a dig session. Before dispatch,
integrate exact tool/quest observations, the full visible physical return route,
post-hex carrying capacity, guardian escape, trap recovery, persisted audits,
and exact-object pickup/turn-in. The pickup controller now saves a unique
selector from the fresh room listing and the matching object's baseline
quantity from DD4's nested `Char.Items` payload, then returns exactly one
`get #selector` command. It confirms possession only after a newer complete
inventory snapshot increases that source-unique description by exactly one;
the selector is not expected in inventory. Checkpoint schema 3 persists the
pending pickup intent so a restart never blindly issues it again. Older
`object_acquired` checkpoints are downgraded because they lack quantity-delta
proof. This proves carriage only; it does not prove quest turn-in or
completion, and it is not yet called by the live runner.
`build_source_hoard_execution_plan` now composes the narrative-verified quest,
carried source tool, source-fuzzed shop level, dig budget, return route,
movement circuits, and direct-trap/guardian damage windows. It is source
planning only: it does not authorize a route or issue `dig`. The first live
version may complete an untrapped hoard and must stop on a trap until recovery
and physical return are verified; do not remove the campaign blocker before
exact-object pickup, turn-in, and timed restart/recovery cases are integrated.
Room-wide physical trap damage uses full AC, not the single-target AC/4
formula. Saved controller tests are unrun; compilation alone does not release
the existing hoard blocker.

`training-travel-supply-20-29` may acquire one pure-invisibility potion for an
observed, affordable advanced-teacher lesson blocked by source route hazards.
Require matching level/reboot training evidence, a recovered healer checkpoint,
nonnegative fame, food, carrying space, and a source-safe ground vendor route.
The vendor must have one stationary reset, no aggression or program, and only
audited noncombat or combat-only specials. Keep private, solitary, no-recall,
randomized, and flight-dependent routes closed. Ordinary city program checks
and source-validated detours still apply.

Use a fresh complete shop listing, one exact TARGETMODE selector and unique
source description, a usable live level, and a price below the current balance
minus 100 copper. Buy once; require acknowledgement and increased inventory.
Replies have a five-second deadline. Record quotes, outcomes and selectors in
`campaign_source_purchases`; persist `campaign_training_travel_supply` at segment
start. Its first, legacy 100-copper cap may reopen once only for the exact saved
unbought quote failure with a larger available budget. Revision 2 consumes that
repair; successful, attempted-buy, identity, transport and other failures do not
reopen it. Acquisition grants no XP or trainer-travel permission.

`consumable-training-travel-20-29` independently registers one noncombat teacher
visit after that completed purchase. Require the same level/reboot lesson audit,
a unique carried source potion, a stationary class teacher with useful gains,
and an exact, recallable ground route of at most 90 source steps. Keep a
20-movement reserve above the remaining source cost, using actual current
movement rather than assuming the character's maximum. Persist
`campaign_consumable_training_travel` before dispatch; never repeat it on
reconnect. Revision 1's exact missing-selector setup failure may reopen once
only when its saved result has no selected potion, route index zero, and the
same still-carried item and teacher. Persist setup revision 2 before that
repair; any other failure stays closed. Empty shop activity must not overwrite
prior purchase evidence. A confirmed purchase remains provenance after a reboot
or level change, but a new journey still needs a current matching training audit
and fresh inventory. Enable TARGETMODE and confirm the live reboot and practice
balance before consuming. Check the city greeter before drinking at the healer.
Require a fresh inventory selector, quaff acknowledgement, inventory reduction, and a
new GMCP invisibility affect of at least four ticks; all replies have five-second
deadlines. Duplicate GMCP inventory suppression is not evidence of absence:
the request-local text listing must match the carried selector. DD4 `save.c`
loads carried objects with target ID zero, so after login a single source-unique
keyword may replace the numeric selector. Its prefix must match no other source
object keyword, and exactly one current carried description must agree with
the complete live inventory listing. Alternatively, one single keyword may be
unique among carried items: require identical complete text/GMCP inventory
counts, one source-unique target description, source mappings for every carried
description, and no matching keyword on any other possible carried prototype.
Unknown or renamed descriptions, duplicates, conflicting aliases, and listing
mismatches reject this fallback. Quoted multiword names do not work here:
`do_quaff` reaches `get_obj_carry`, which uses single-prefix `is_name`.
Setup revision 3 may reopen revision 2's exact unselected, unconsumed, route-index
zero failure once when the current source and carried inventory prove this
keyword method. Require matching item and teacher evidence, consume the marker
before dispatch, and retain all route, practice, inventory and affect checks.
Never reuse a saved numeric selector.
Carry `campaign_training_travel_result` into later checkpoints. If a legacy
checkpoint lost it, load only the latest matching trainer segment through the
256-row metadata lookup. Restore only a completed healer result whose full
attempt marker, level, boot, item, teacher, and setup revision match the current
marker. Preserve explicit later results, including nulls; restoration records
its run ID and is evidence recovery, not retry authorization.
Only the prompt after the expected reply header completes that request; an
earlier configuration or room prompt cannot acknowledge inventory or quaffing.

Only this noncombat teacher executor may use equipment-aware invisibility to
pass source-known, non-detecting equipped aggressors. Programs, detecting gear,
unknown objects, unsafe specials, private/solitary/no-recall rooms, randomized
exits and flight-dependent paths remain closed. At every step require the exact
live exit, at least two invisibility ticks, health, and remaining movement.
The exact route's reserve replaces the ordinary half-full movement floor, not
health recovery. Any change ends the visit and returns to healer 3054. Buy at
most three useful source-capable lessons using fresh practice listings, then
recall and recover. Save `campaign_training_travel_result`; accepted lessons
and useful later XP remain separate proof gates. Runs 15523/15524 and 15916
proved bounded pre-consumption rejection only. Run 15920 subsequently proved
the zero-ID keyword path: `quaff elixir`, confirmed invisibility, the complete
80-step teacher route, three accepted lessons, and full healer recovery at
checkpoint 48408. Its live listing confirmed enhanced damage 67%, defense
knowledge 63%, and parry 62%. Preserve both the failed and successful evidence.
Saved regression cases remain unrun under the October 2 daily limit.

DD4's `do_inventory` appends `You are carrying N/M items.` after its listing;
that total includes worn gear. Ignore only this exact terminal footer when
matching inventory counts, not unknown lines or extra items. Setup revision 4
may repair revision 3's unselected, unconsumed, route-index-zero failure only
when the same completed healer segment's bounded 64-event tail proves an actual
inventory request, a complete matching text/GMCP listing with that footer, and
no quaff before the request ends. Match the entire attempt marker and saved
result; persist its run ID as `inventory_footer_repair`. Current source keyword
uniqueness, fresh live inventory agreement, and every existing route gate still
apply. Consuming revision 4 closes this repair; it is not a general retry.

Local fallback training retains the registered class-teacher route and its
hazard checks. After the normal lesson selection is exhausted, the same visit
may buy another distinct registered priority only when the fresh listing,
remaining practice balance, current stats, and exact source teacher predict a
positive gain. Stop at three accepted lessons, refreshing `practice` after
each acknowledgement; never invent the resulting percentage. A live listed
zero-percent skill can justify a lesson, unlike an absent or inferred skill.
Persist `lesson_policy_revision` in local-fallback evidence. A consumed legacy
visit without that marker gets one fresh attempt only for a newly learnable,
source-capable skill at the same teacher, level, and reboot. Consume it before
dispatch; neither failure nor reconnect reopens it or clears combat losses.

Before leaving the healer for a distant class trainer above level 10, require a
fresh observed skill listing and practice balance, complete live stat modifiers,
and the exact registered source teacher's capacity. Apply DD4's practice-gain
formula to the eligible automated priorities. Skip the distant trip only when
all of that evidence proves no lesson can gain a percent; incomplete evidence
retains the existing route. This check does not suppress explicitly required
practice or separately gated maintenance.

A consumed local teacher fallback can receive one separate route-clear recheck
per level and reboot only when its actual run confirms the exact teacher,
pre-departure city hazard, and no attempted or rejected lesson. The latest
successful source hunt must have gained net XP and recorded its own completed
city locator, with positive source-known locations outside every teacher-route
room. Inherited checkpoint sightings do not count. Require a recovered healer
checkpoint and a fresh source plan with useful, affordable lessons; preserve
all combat-loss evidence. Save blocked/observation run IDs and route rooms in
`campaign_training_deficit_repair.local_teacher_fallback.route_clear_recheck`;
consume its pending status at segment start. The normal live trainer preflight
still decides whether to leave, and another block ends this recheck.
The same retry may instead use a later successful automatic `world-time-probe`:
require its actual `time` command and connection-local matching boot response,
unchanged level, no net XP loss, and timezone-aware segment timestamps showing
at least 300 seconds between the blocked visit ending and that probe starting.
This breaks the dependency on a productive hunt before improving readiness.
It does not claim the route is clear; the ordinary trainer locator must still
prove departure. Record `reason: bounded-route-cooldown` and `cooldown_seconds`
in the shared retry marker. A spent clear-sighting or timed retry excludes the
other. Missing time or boot evidence cannot reopen it.
When the blocked visit is no longer in the recent eight-segment tail, use
`get_latest_campaign_segment_for_phase`: scan at most 256 narrow metadata rows
under that campaign, then load only the chosen row. It needs no new phase index
and never expands the runtime history payload window.

Ordinary `consider` replies have a request-local 2,000-character buffer and a
five-second response limit. DD4's absence reply, `They're not here.`, completes
the pending request and enters the existing bounded target-refresh path, even
when split across reads. Retain that absence until a new request; later room
chatter must not erase it. An unanswered check ends the hunt through normal
combat/death recovery and healer logout, without inventing absent or below-band
evidence. When a combat name differs from a room description, a flee
may match the source short name only through a fresh, same-room, same-level,
same-boot encounter identity for the registered prototype; pursuit bounds and
destination checks remain unchanged.

Field `where` replies retain the request-local 8,000-character buffer until
the prompt after the listing header arrives. A first matching row cannot
complete the reply or discard later matching locations. An explicit absence
reply still completes immediately. If the existing 1.5-second grace expires
without a complete field listing, use the bounded watchdog return; record
neither absence nor below-band evidence. Preserve up to sixteen locator
decisions in `campaign_fastwalk_where_decisions`: reported locations, their
registered room mappings, remaining endpoints, and any chosen relocation.
These records explain navigation only and cannot authorize combat or enlarge
the registered safe search graph.
After a positive locator takes the player beyond the initial search origins,
an exact matching source prototype may continue along a forward suffix of an
already-audited relocation path containing the actual room. Preserve waypoint
mode, reported destination labels, empty-room evidence, and the existing retry
cap. Never reverse a path or join fragments to invent a connection. Record the
original route origin with the selected suffix. When no usable relocation
remains, or the one same-room recheck is spent, close that locator until its
scope changes; do not spend its remaining budget repeating an unchanged query.
Treat a positive-location rebase as a detour, not a replacement circuit:
insert its inspection immediately after the current stop and preserve the
original unvisited stop suffix. If the destination is empty, continue that
registered suffix instead of jumping to the end of the itinerary. Before
continuing, re-root only the first unvisited VNUM leg from the exact detour
endpoint to that same registered endpoint, using a bounded source-safe bridge
and live GMCP exits; keep later stops unchanged. Never replay its old
origin-relative VNUM sequence or widen the allowed room graph. If no safe
bridge exists, return with the route evidence intact.
If that selected path crosses an already registered recovery endpoint, split
the relocation at the exact endpoint and retain its targetless transit stop.
Do not copy recovery permission to the origin, an off-path room, or an
unresolved command-based route. The normal live empty/no-mob, health, movement,
and timeout checks still govern sleep and continuation. Record retained
`recovery_waypoints` with the locator decision; never replace the entire path
with a combat stop that silently loses the recovery boundary.
Campaign revision 338 may reopen one exact source-ranked wanderer result when
its saved segment ended safely at the healer after `where` positively located
the target but the old relocation graph had no endpoint left. This repair
requires the same level, boot, and DD4 source revision; positive mapped locator
evidence; full healer recovery; and no kill, death, combat, or policy-specific
XP loss. It preserves the superseded result and locator decision, consumes its
marker before dispatch, and retries navigation only. The corrected direct
rebase and all current source, live-exit, hazard, identity, isolation, consider,
output, and action-budget gates still apply. A second miss closes the route.
Closed markers for a different exact policy, level, boot, or source revision
must not suppress a new eligible result; retain them in bounded revalidation
history. A pending or attempted marker in the same level and boot remains the
only active locator recheck. Evaluate this repair on every campaign resume,
after loss evidence reconstruction, rather than only during a policy-version
migration.
After a useful ordinary source-ranked kill, an unarmed, non-aggressive wanderer
with no special, program, or loot contract may receive another fresh locator
query within the original segment kill cap and source spawn capacity. Require
positive exact-prototype XP evidence, only accepted considers, and the ordinary
health, mana, movement, provision, and no-loss boundaries. Protected, familiar,
resource, and damage-window probes are excluded. Reuse only registered paths
and the existing locator budget; the next encounter must be isolated and receive
a new live selector and consider. Record `after_objective_kills` on the selected
relocation. No further mapped destination ends a productive search normally,
without marking the target unavailable or revisiting the just-cleared room.
An optional outbound interception must retain the original unvisited stop even
when the intercepted stop is last in the circuit. After a pre-combat crowd
rejection, restore that earlier stop and continue only the remaining official
outbound commands. Preserve crowd evidence and the completed-interception marker;
do not retry the crowd, authorize combat, clear a route abort, or resume a
completed, failed, or already-returning journey.
Registered Mirror Guardian hunts and research retain the fixed approach only
through room 19031. Source `R` resets shuffle rooms 19032-19040: derive the
existing bounded live-navigation graph from current source, reject source
hazards, and finish at exact room 19041 using observed GMCP exits. Both navigation
indexes refer to the end of that preserved approach. Never execute the old
fixed north commands inside the maze or record an absence from another room
as if the target endpoint had been reached. The route grants no combat override.
When continuing from room 19041 to the second registered reset in room 19031,
derive reverse live-navigation preferences from that same route metadata and
follow observed exits back through rooms 19040-19032; never treat the
source-static waypoint list as proof of randomized exits.
Source absence records require an observed room, never a fallback to the planned
destination. For a purely destination-guided stop, that room must be its actual
endpoint; an unfinished or misdirected route cannot spend the endpoint search.
If the level-26-to-30 Guardian hunt safely aborts because live GMCP has no exit
to room 19036, persist that exact route failure for the current boot only when
the segment began and ended at the same level and boot with no kill, death, or
XP loss. Preserve any earlier probe evidence, but do not let it reopen this
route; rotate to the Shire battle-master probe. A new boot may probe the route
again under the ordinary live navigation and combat gates.
After a bounded route-program wait, finish ordinary healer recovery before
leaving. Consume the pending wait at departure and clear the completed emergency
return, so the next step performs a fresh route check. Recovery alone cannot
consume another hazard attempt. Combat, loss, death, explicit logout, and runtime
boundaries cancel the retry without clearing their return evidence. Preserve
the existing retry limit and all subsequent live hazard checks.

Room-listing headers retain balanced closed-exit markers such as `[up]` inside
`[Exits: ...]`. Familiar identification still requires the completed listing,
one exact source-matched selector, and a positive group acknowledgement. While
that preparation is pending, suppress the ordinary route-complete fallback;
only its existing confirmation deadline or an actual safety boundary may end
the wait. A quiet decision is not a completed route.
For a failed route that has safely returned, retain its matching terminal
familiar-preparation, withdrawal, and combat-timing evidence in the campaign
checkpoint. Older preparation records must not replace the failed run's audit;
the saved selector and group state remain diagnostic only on reconnect.
Familiar-backed route selection and combat share the random-withdrawal audit:
each possible encounter room needs an NPC-usable exit, and every usable exit
must exclude source aggressors, attack programs, unsafe specials, and possible
fight joiners. Include full source wandering reach, not the short target-search
budget. Recheck the actual live encounter room before ordering the familiar;
a safe reset room does not authorize a displaced encounter.

Combat-pouch audits at departure, repacking, and logout share a bounded reply
buffer. Require the complete contents listing before replacing either potion
ledger; unrelated room or healer text is not an empty-pouch observation. After
five seconds without confirmation, preserve the previous ledger and return to
healer logout without hunting or retrying the audit. A confirmed empty listing
does clear old quantities. Newly discovered potion keywords still require the
existing source-safety checks; ambiguous potions require retained provenance.
Treat a completed DD4 prompt as a line boundary before matching the pouch
header: unsolicited healer output can place that prompt immediately before
the actual reply without a newline. Preserve the complete-listing requirement.
If the check starts partway through that preceding prompt, retain only its
recognized unfinished prompt prefix from the bounded current-line tail. Never
seed a new audit with old listing contents, a complete prompt, or unrelated
text. Clear the tail on disconnect; an incomplete new listing still cannot
replace either inventory ledger.

When choosing a loose combat potion, skip keywords already attempted in that
preparation and potions deliberately evicted to free a sanctuary slot. Continue
to the next source-safe carried potion instead of letting the first skipped
healing potion end preparation. Require the existing eviction acknowledgement
before stowing; missing replies retain the bounded abort, and only acknowledged
placement adds a pouch reserve. Run 16448 live-confirmed `get ochre beltpouch`
followed by `put all.purple pouch`, correcting runs 16446/16447's wasted travel.
This changes packing only, not sanctuary admission or combat authorization.

One later source-ranked retry may be armed for the exact five-second pouch
timeout only when the same-boot, same-level result has no target, consider,
absence, crowd, or XP-loss evidence and exactly one current-band autonomous-safe
candidate matches. Keep that marker through healer and other maintenance
segments and unrelated source-ranked hunts; consume it only when that exact
policy is dispatched, and close it after the attempt whether or not it kills.
This does not retry a pouch audit inside the failed run or relax any route or
combat gate. When the exact policy is present only in the same-boot
city-route-attempt ledger, this one retry may pass that attempted marker; any
city-blocked or caller-excluded policy remains closed, and the new segment
must perform its live route preflight again. The split-color prefix repair has
captured-transcript and offline-test coverage; a live retry remains unproved.

Gear acquisition uses the same per-category capacities as stance selection.
Compare a candidate with the weakest selected slot, or an empty slot, after
including carried alternatives. Preserve actual duplicate-item quantities, but
never add the structured equipment snapshot to its duplicate textual summary.
An improved rank is not permission to bypass source route or combat gates.
Never derive a live `n.keyword` selector by numbering every prototype in the
world source catalog. DD4 resolves that ordinal against the current carried
items or shop listing; use the exact item's source keyword, then require the
fresh `eq all` result to confirm a wielded or worn upgrade.

Weapon prototype values are not live damage dice. DD4 `create_object` generates
minimum/maximum damage from the loaded level, with two fuzzy rolls per endpoint;
`one_hit` draws uniformly between those live values. Source gear ranking uses
the conservative generated floor, never the prototype's apparent dice product.
Keep that estimate separate from an identified instance, especially constructed
or body-part weapons. Telnet `Char.Worn` does not supply damage endpoints, and
legacy `instance_id` zero does not uniquely identify an item. Human `identify`
requires an inventory object: remove the exact worn weapon while awake at the
healer, identify it, and re-wield it with confirmation before leaving. A generic
scenario's completed status alone does not confirm `quit`; require the farewell
or use the existing bounded return-home worker to finish recovery and logout.
For ordinary field preparation, the registered `identify` action requires a
positive observed proficiency, healer room 3054, standing, no combat, sufficient
mana plus reserve, one source-known removable weapon, and an unambiguous command
keyword. Permit one inspection per connection, with five seconds per reply.
Read the complete name, level, and min/max damage; confirm `wield` and a fresh
`eq all` listing before using that reading. On identification timeout, make
one rearm attempt; a failed rearm ends the hunt at the healer. Armour changes
do not invalidate weapon identity, but weapon removal, disarm, a changed worn
record, or reconnect do. Persist `campaign_weapon_damage_audit` for inspection
only; it never authorizes damage on another connection, including positive IDs.
The pre-login estimator uses generated floors, with the existing independently
audited natural-form damage contract kept separate. Live encounter budgets may
use the confirmed reading without changing route, HP, or finite-action gates.

Pre-level equipment may narrow the existing ten-percent-of-level window only
for source-known, plain, unequipped single targets without a familiar, gate
fight, or admitted bystander. Include the area and inherited mobile XP
modifiers, source level fuzz, best ordinary popularity/random reward, full HP
damage credit, regeneration over the bounded worker lifetime, and final-hit
allowance. Unknown source syntax, rank, specials, or output retains the original
window. Keep each level/target window monotonic during the connection so a gear
swap cannot oscillate its own threshold; save `pre_level_gear_windows` as
diagnostic evidence only. Reevaluate before each encounter, retain recovery
precedence and ordinary stat-training preparation, and never swap while asleep
or fighting. This is reward planning, not a promise about every possible XP
source and not permission to change combat or route gates.

While the project is active, run exactly one regression batch each local
calendar day. Use focused tests for routine changes or the full suite at a
coherent milestone, never both on the same day.
Record it before starting in ignored `runs/regression_test_batches.json`, using
the Pacific/Auckland calendar date, and record the outcome afterward. A failed
batch consumes the day's allowance; do not rerun tests or start another
regression batch that day.

When flight funding is unavailable, a fresh ground search with no eligible
target may hand over to the next registered current-level policy even if the
three-attempt ground budget is not spent. Preserve its count and the funding
marker; never consume empty attempts to unlock an alternative. A pending exact
locator retry remains first. Quest fallback and cooldown waits are available
only when a source-derived next-level QP shortfall blocks progression; with no
shortfall, skip optional questing and keep selecting current-band XP. Once a
QP gate is active, retain the live assignment and `nextquest` cadence gates.
Ground funding fallbacks and their rotation must retain the main selector's
bounded capacity-only admission, including its independently audited route
program allowance. Recheck the current band, movement, kill count, protection,
and below-band evidence. Other source rejections and live crowd, identity,
consider, and combat limits remain unchanged.

An otherwise selected hunt that needs sanctuary may reach the bounded quest
request only when a source-derived QP shortfall blocks the next level and its
reserve/recovery attempts are exhausted. Require a recovered healer checkpoint,
carried food, observed quest status, nonnegative fame, no active quest, and a
zero live timer. Preserve sanctuary counts and protection evidence. Any assignment still needs its own source
route and combat approval; rejection returns safely, and DD4's cooldown
controls when another request becomes eligible. Run 15527 exercised the
handoff but abandoned its unsafe assignment, earning no XP. New checks are
saved, unrun.

Selection alone does not spend the quest request. Record dispatch only when
the command is actually sent; after an ambiguous interruption, obtain fresh
quest status before deciding whether to request again. An active assignment or
positive `nextquest` closes the request gate. A later zero timer reopens it,
regardless of earlier campaign request markers. If a request made at zero has
no assignment but DD4 starts a new positive timer, that is a fresh cooldown
cycle, not a per-level or per-reboot cap. Clear the prior wait marker, stay at
the safe healer while the new timer runs, and request again as soon as it
reaches zero. A stale earlier countdown must not prevent a live timer refresh.
This grants no movement or combat permission.

A completed current-boot funding kill with a pending purchase/funding marker
must liquidate new saleable loot before waiting for an ordinary loot batch,
even when carried coins exceed a provisional purchase-price estimate. Keep
the retained-inventory baseline and shared city-shop route checks ahead of
this priority; neither unchanged gear nor a blocked crossing grants a retry.
Only observed sales count as funding proceeds. A selected sale also precedes
the pending flight-purchase preference: converting loot cannot spend the
coins reserved for that purchase, and an estimated price is not a live quote.

Routine repository, source refresh, tests, live runs, and exact process audits
are already authorized. Use ordinary available tools; do not ask again or
manufacture an escalation. If an external permission review times out, retry
once promptly, then defer that operation and continue useful local work. Never
wait indefinitely for an invisible review or repeatedly poll unchanged failure.

At the 9:00 PM Pacific/Auckland checkpoint, make at most one local commit
attempt per day: commit a coherent, reviewed change set only. The user handles
all remote pushes and merges; never change a remote unless explicitly asked.
Bound the local attempt to 60 seconds. A failure consumes the day's attempt;
record it and do not retry for 24 hours. Do not commit unrelated or unreviewed
worktree changes. Record the attempt and next eligible timestamp in ignored
`runs/local_commit_attempt.json`, including success or failure when no commit
was created. Use native filesystem operations and verify absolute targets
before any recursive move or delete.

Read-only campaign selection probes must load the same source world, gear
catalog, and relevant history as public startup. A missing inspection dependency
is not a live capability defect. Inspect returned tool results before composing
the commentary that reports them; do not combine dependent evidence queries
and prewritten conclusions in one tool batch.

Use `python -m dd4tester show-combat-readiness --level N --class CLASS`
for a bounded, offline view of the current output envelope, durable campaign
constraints, source-band targets, gear blockers, and quest readiness. The report
keeps GMCP alignment and fame separate and shows the questmaster route, quest
point level gate, and whether a fresh request is source-eligible. Add
`--character NAME` and `--all-areas` when comparing a saved campaign across the
full source map. It also exposes DD4's ordinary +6-or-higher fame rule and the
current bounded research horizon, alongside
the separate `ACT_IS_FAMOUS` usable band, with source candidates and their
output or safety blockers. This report is diagnostic only; it never grants live
dispatch permission.

The report's `output_fit` field is only the offensive source HP-ceiling check.
`source_gate_fit` combines source safety, source-level band, HP admission, and
sanctuary availability. It is not the campaign's final dispatch decision: it
does not include every live route check, same-boot consider record, target
cooldown, or current useful-XP probability. The report shows useful-XP
probability and known below-band or invisibility blockers where available, but
these fields remain inspection evidence and never authorize a live route.

Refresh the DD4 source periodically, roughly daily during active work. Use a
bounded ordinary pull, preserve source pins and revision evidence, and defer
network failure rather than blocking development. Source area files and C code
are legitimate game knowledge. Never modify the upstream game to make a test pass.
Area section boundaries use `boot_db`'s actual header vocabulary, including
ambient/sound and object-set sections. Hash-prefixed ASCII maps inside room or
mobile descriptions are not headers. Preserve the complete room graph, exits,
flags, resets, and special procedures; newly parsed rooms grant no exception
to route or combat checks. The October 2 correction restored 492 Underdark
rooms. Its formerly missing quest route remains blocked by real companion and
special-procedure hazards, not a missing source graph.
When an unavailable quest room has an analysis-only path through locked doors,
report its required source key VNUMs separately from a disconnected map. Never
dispatch that analysis path or treat a key listing as possession or acquisition.
For the October 7 TenTusks scroll assignment (quest room **25530**), source
proves a narrow key chain: object **25404** is carried by octopus mobile
**25405** in underwater-ground room **25426**; giving it to statue **25408**
in room **25429** creates key object **25405** and unlocks north. Mobile and
object VNUMs are separate namespaces. This explanation is not an executable
quest route. The recall-to-carrier source path is 53 commands and crosses
aggressive cave beasts **25402** in rooms **25412** and **25418**. The carrier
room is underwater-ground: `update.c` initializes air supply to two and begins
drowning damage on the second underwater update without `breathe water`. Source
lists a breathe-water philter (**3389**) in Midgaard's Magic Shop, but stock,
price, and a fresh live breathing effect must be verified before entry. Even
with the key, the 63-command shortest route to room 25530 has further source
hazards, including the fire serpent and molten uzuz; each needs its own live
route and safety admission. Never convert this chain into a blanket exception
for aggressive transit, specials, water, or locked doors. See
`docs/QUEST_ROUTE_AUDIT_2026-10-07.md` for the run-specific evidence.
Source refreshes clear source-derived routes and cooldowns, but preserve exact
XP-loss records and observed absent-target results from the current MUD boot,
along with the matching absence cooldowns. A local source update must not erase
live evidence and silently reopen a failed fight or an expensive empty route;
evidence from an older boot is discarded. Preserve a same-boot loss as a block
on that exact hunt, while dropping old target-HP and route-only retry evidence;
stale source estimates never authorize a retry.
The estimator mirrors the pinned source's inherited and area `MobHPMod` and
`MobDamMod` scalars. `MobDamMod` is applied to each positive NPC attack before
sanctuary or critical arithmetic; an unresolved scalar is a hard rejection for
combat and transit budgets. It also credits `fight.c:do_knife_toss`'s
eye-dependent face-hit double only when parsed target body-form evidence proves
eyes; unknown anatomy remains uncredited.
Area headers are parsed with the same distinction as `db.c:load_area`: the
first two values describe the display band, while the third and fourth values
are the movement-enforced low/high gate used by `act_move.c`. Candidate
endpoints and resource routes are rejected when the character cannot enter a
room at the enforced level, and `-4 -4` safety areas remain inaccessible to
ordinary player characters. A display band is evidence for ranking, never
permission to dispatch a route.
The source Circus flight reserve begins with `buy ticket`. DD4's `do_buy`
rejects all shop purchases while fame is below zero, so a live ticket refusal is
recorded as `reputation_blocked` and cannot be reopened by `--retry-stalled`.
For negative-fame recovery, the only current gas-special exception is the
source-famous Green Dragon mobile **6112**. Its admission requires the exact
`spec_breath_gas` procedure, sanctuary, a source-validated route and HP budget,
and healer mobile **3012**'s `spec_cast_adept` recovery, which can cure the
resulting nausea through `cure poison`. This permits one bounded GMCP damage
probe; after sanctuary is observed, that exact contract may use the existing
finite **36-action** live horizon. The ordinary twelve-action estimate still
governs admission before sanctuary. This does not authorize generic gas
breathers, scripted specials, or an unbounded fight. Run **13407** measured
Green at **576 HP** versus Kestrel's **342-point** conservative output ceiling;
the bot withdrew before a losing exchange. Run **13408** repeated this
bounded branch after the reboot-local preparation: the first stopped at that
live HP/output gate, while the second quaffed sanctuary, observed the expected
gas special, withdrew, and recorded a **385 XP** loss before healer recovery.
Neither run produced a kill or fame change. Revision **302** fixes the separate
handoff that previously failed to carry an eligible improved-output retry into
the protected live stop; a live kill and fame change must still be recorded
before any policy is treated as proven.
The current ordinary fame search uses a bounded +9 research horizon, but DD4's
actual rule is `victim.level - player.level > 5`, or at least six levels higher,
with no game-enforced upper limit. Revision **305** additionally permits a
plain candidate whose source HP range crosses the player's maximum HP when
sanctuary is verified and the audited player output covers only the source
lower bound. The resulting stop is sanctuary-backed and always requires a
live GMCP HP/damage-window probe. A plain, unarmed current-band target may
also receive one unprotected version of that probe when its source HP range
fits the audited output: if the whole range is below the player's HP ceiling,
the upper bound must fit; if it crosses that ceiling, both the lower bound and
the uncertainty above the player's HP ceiling must fit one output window. A
passive endpoint does not waive this check. Any transit program must be one
exact low-level mobile that can be located with `where`. A nominally same-level
target may retain one additional level of source load-time fuzz only when its
audited range reaches character level minus two, and its maximum remains
within character level plus two. This does not open armed, special, unknown, or
unresolved hazards. The live target HP ceiling must still fit the finite action
budget before combat continues. A plain, unprotected probe may finish a live
target that falls just short of the warning fraction only when the target's
remaining HP and projected incoming damage fit that same bounded action budget
and health reserve. The exception ends the probe; it does not create a general
combat retry or override a special, armed, crowded, or unresolved target.
For this exact unprotected HP-fuzz probe, the initial live ceiling check may
allow the target through to the existing damage-window measurement even when
its observed maximum is slightly above the total output budget, but never above
the source-audited target HP ceiling. This is only the pre-probe handoff: the
measured remaining HP and incoming damage must still fit the bounded budget
and health reserve before combat continues.
If the first three live samples land at least 70% of the warning threshold but
fall just short, an exact unarmed target may receive one extra two-update
window when the measured exchange is at least as favorable as the ordinary
1.1:1 damage-trade floor. This also applies when incoming damage is zero. The
source action budget must cover both updates, current health must be at least
70% of maximum, and their projected damage must leave the usual field reserve.
This is only more evidence for the same admitted target; the normal output,
health, and live identity checks still decide whether the fight continues.
DD4's `do_consider` health wording compares current hit points. In the general
case, only `you are currently much healthier than` (a lead greater than 100
current HP) can authorize the passive pre-combat fallback when live enemy HP
is unavailable. `currently healthier`, `slightly healthier`, and `teensy bit`
alone do not authorize it. A source-vetted protection-recovery fallback has one
narrow exception: the exact endpoint must be a fixed, passive, unarmed mobile
with no source program or special, and its full source HP ceiling must fit the
audited player damage budget. The candidate must already pass the ordinary
source HP-range, incoming-damage, route, and same-boot attempt gates. This
allows one bounded opener to obtain live GMCP and damage-window evidence; it
does not authorize continuing combat. Run **14041** remains the reason not to
generalize from small health leads: a teensy-bit result preceded zero observed
damage and a **419 XP** loss against the diamond golem. The normal live damage
window and withdrawal path remain authoritative after any permitted opener.
This exact fallback may use a route requiring flight only when the checkpoint
proves active `fly` or `levitation` with enough remaining duration for the
route. That satisfies movement only; it does not relax the endpoint, locator,
consider, health, or damage-window gates.

Revision **324** adds one narrow Mage fallback: a practiced familiar may open
an otherwise sanctuary-gated endpoint when fresh source evidence proves that
invisibility blocks every transit aggressor. The endpoint must be a stationary,
non-aggressive, unscripted source mobile no more than five source levels below
the player, with at most one weapon and an audited staging room. This is a
bounded familiar probe, not a lower-band XP exception; the live target,
damage, output, and route gates still decide whether the fight proceeds.
After an unrelated current-level loss, one plain unarmed target may use the
same bounded probe when the audited output covers its lower HP bound and the
uncertainty above the player's HP ceiling, while the target's source peak stays
below the tighter half-HP limit. The route must be the exact source-locatable
program exception; known transit specials are allowed only when source verifies
noncombat behavior and confirms the mobile has no program or reset-loaded gear.
Unknown or combat-capable specials remain blocked. GMCP HP and the damage
window still decide whether combat continues.

Revision **325** repairs an empty-ground-frontier flight handoff. From a fed,
healthy healer checkpoint with an open Magic Shop route, the campaign may run
the ordinary source selector against a disposable ten-tick flight snapshot.
That snapshot only detects whether a source-ranked current-band flight route
exists; it is never persisted, dispatched, or treated as active flight. If the
selector finds one, the existing bounded flight workflow is chosen. It first
refreshes inventory and may quaff a carried potion only when the source spells,
source-unique keyword or current positive item selector, inventory reduction,
and resulting live flight affect all verify. Otherwise it follows the existing
fresh-price purchase path. The campaign reranks from real live state afterward,
so normal route, target, consider, output, and survival gates still control
combat. Offline coverage was added on 2026-09-30; it was not rerun because the
daily regression batch was already used. Dorrik's live handoff and carried-potion
activation remain unproved.

The reconnect path keeps two facts separate: `checkpoint_has_flight` is live
affect evidence, while `has_flight` may only mean that flight can be
reacquired during the new connection. A current-band Catacombs candidate may
therefore be discovered with the disposable snapshot even when the selected
policy still has to buy and verify flight before departure.

Run that same bounded snapshot before closing a frontier when its best ground
candidate is removed by an exhausted sanctuary gate. For this handoff, require
the hypothetical-flight selector to find a separate current-band candidate
that does not require sanctuary; otherwise continue to the existing bounded
quest or unavailable path. Preserve the exhausted sanctuary marker and every
ordinary live route, identity, consider, output, and survival check.
Campaign policy revision **336** records this selection change. Focused positive
and negative regression cases were added on 2026-10-01; they remain unrun because
the daily regression allowance was already used. `show-campaign` now includes
each listed no-sanctuary option's same-boot result and explicit retry blockers;
these remain diagnostics, never authorization to dispatch.

Revision **306** carries the source-recorded upper level bound into every
generated stop for an exact sanctuary-backed required-loot gear carrier. This
is route construction only: it does not authorize unprotected combat, broaden
ordinary progression, or alter the strict +6 fame threshold. Live acquisition
remains unproved until a run records the item and return state.
Runs **13259-13260** made two bounded Moria sanctuary-resource attempts and
returned safely without a carrier. Live run **13261** exercised the permitted
post-reset recheck and again returned safely without a carrier; run **13262**
completed a food-reserve segment without XP change. The all-area source audit
finds no other executable level-24 sanctuary reserve; later source placements
begin at level 27 or require routes that are not audited safe for this
character. Treat checkpoint **41449** as a durable resource frontier, not
permission to replay the exhausted route. Run **13275** is the current live
proof that the reconciled policy opens the full 11-stop Moria route through
rooms 4064, 4152, 4071, and 4074; the carrier was absent, so the route remains
unproved for resource acquisition.
Run **18252** exposed a locator stop after a confirmed below-band route-gate
kill in Maze room **4058**: the generic post-fight guard closed the required-
loot search. The exact room-4064 purple-potion hunt may resume its locator after
only confirmed kills from its audited route-gate VNUMs, while in a source-mapped
Maze room and within the existing eight-query limit. This resumes searching;
each fight retains its original live identity, consider, route, output, and
survival gates.

Policy revision **303** makes healer recovery explicit when a checkpoint in
room **3054** still has active poison. The exact reopened Forest
gear retry may proceed after that recovery despite the old level-24 protection
marker, but only once and only for the source-identified claw objective. Run
**13277** cleared Kestrel's poison at the healer. Run **13278** found the
Kodiak in the River bed, encountered a live poison-swarm crowd at gate room
**18027**, withdrew, retried once after healer sleep, and withdrew again without
XP loss or claw acquisition. The marker is closed for this reboot.

## Live Sessions

Use indexed latest-state lookups for terminal run outcomes, not full transcript
loads. Completion/runtime-cap and failure lookups have independent precedence;
retain the entire selected payload, explicit empty kill ledgers, and newer
events. Do not cache terminal absence or remove loss history to speed startup.
Measure public startup separately from query benchmarks and distinguish cold
from warm reads. Faster inspection is not XP or combat-readiness evidence.
On databases larger than 1 GB, startup deliberately skips building the
campaign-phase index and uses the bounded durable segment tail for loss
repair; schedule that index migration separately rather than blocking a live
resume on multi-gigabyte SQLite maintenance.
When a checkpoint contains an observed training listing for the current level
and reboot, use that compact audit as the skill capability source; do not replay
up to 4,096 historical segments. Keep the legacy event backfill for checkpoints
without that evidence, and retain visible preparation boundaries so a shared
SQLite database cannot make a live launch appear hung.
Source policy selection must reuse the immutable world catalog loaded during
campaign setup; do not reparse all area files for each selector fallback. Emit
level-aware preparation progress before expensive frontier passes, and keep
those passes bounded by the campaign outer deadline before opening gameplay.
After a source-audited crossing into one neighboring area, retain only locator
routes rooted at the new room and already vetted within that area. Allow at most
one further locator refresh and clear the neighbor-crossing fields; exact
in-area routes remain usable, but a second area crossing is never implied. Run
**14504** live-validated this path: a Dragon Cult miss routed through Midgaard
rooms **3024, 3025, 3026, 3045, 3046, and 3219** to the guild, where Ararisa
earned **240 XP** and returned safely. The focused neighbor-locator test covers
both populated and empty source-mapped routes.
When startup already has the newest campaign-segment tail, pass it to
interruption and timeout cleanup; status-only scans over the full JSON-heavy
segment table are not an acceptable live-resume path. On the shared large
database, the runtime tail is capped at eight newest segments so cold startup
does not materialize hundreds of large JSON states before a live socket opens.
When reconnect reveals a verified same-level XP drop, retain it as a campaign
loss lower bound even without a captured penalty message. Do not add it twice
to explicit loss counters, infer a death or command-level cause, or reopen a
failed hunt while repairing the counter. Use saved per-segment baselines for
idempotent history repair.
Damage-window trade checks compare target damage after observed target healing
against player damage net of observed in-window HP recovery. Future health
reserve projections still use gross player damage, so a single recovery tick
does not make the bot assume healing will continue.
Starter combat identity parsing must treat DD4's source-format swing messages
("grunts as ... takes a swing at you", "grunts and swings at you", "takes a
swing at you", and "stops swinging ... and swings at you instead") as incoming
combat. Preserve the planned endpoint target and continue through the normal
live consider, source VNUM, isolation, and damage gates; this is recognition
evidence, not permission to bypass them.
For a pending `kill` opener, a matching target's "dodges your attack" or
"parries your attack" line also confirms that the opener resolved. Keep the
normal combat wait before dispatching a between-round skill. This does not
acknowledge spells, unrelated mobiles, or incoming NPC attacks; all target,
output, and survival gates remain in force.
For a source-ranked spell action in a room with exactly one current GMCP enemy,
use that live enemy's displayed name when matching the action response. The
campaign keyword and DD4's combat display can differ (for example, `human boy`
versus `The stunned boy`). In a crowded room, retain the exact source/target
identity; never accept a generic damage line as acknowledgement.
The streaming text path must also retain an incomplete ANSI escape when a
Telnet response splits between chunks. Reassemble that escape before prompt
and area extraction; otherwise a valid endpoint room can be recorded with a
corrupted area name and the worker can reach its runtime boundary while
waiting for an acknowledgement that was already on the wire. This is a
transport/parser repair only and does not grant target or combat permission.
When a successful combat recall returns the character to the Temple of
Midgaard without an explicit combat-end line, clear the local combat target
and combat-active flags before issuing the healer-room recovery step. A stale
local target must not cause repeated recall commands or a watchdog failure;
the live room and enemy state remain authoritative.
For a familiar-backed source probe, an aggressive or scripted endpoint must
also have a source-audited outdoor no-mob staging waypoint on the outbound
route. If no such waypoint exists, reject the policy before travel; do not
enter the endpoint and hope to summon after an automatic entry attack.
Also reject a private destination with a source-reset mobile: DD4 checks room
occupancy when the follower enters, so the target and player can prevent the
pony from following even though the player entered successfully.
For an ordinary source-ranked candidate whose endpoint aggression is blocked
only by invisibility, require the learned class/subclass `invis` path and
enough current mana before selecting the candidate, including for capacity or
level-ceiling research. Reject it before opening a socket when that preparation
is absent. The separately audited familiar-probe contract is an explicit
alternative; unrelated route aggression and sanctuary recovery do not imply
invisibility permission.
Sanctuary attempt reconstruction must be idempotent. Rebuild the supplied
segment history separately from the current saved counter, seeding an omitted
prefix from the first segment's start. Retain a matching saved count as a floor
unless positive acquisition resets it. Replaying the same or overlapping window
must not add attempts; a world-time probe is not a resource hunt. Preserve
existing failure/loss evidence and do not silently lower legacy inflated counts
or reopen a terminal route while fixing replay. Such correction or revalidation
requires its own authoritative evidence.

Run gameplay serially until concurrent validation proves the shared-database
boundary. Before launch, check for an existing gameplay worker. A tool returning
a session handle means it is still running: inspect or resume that exact handle,
not a duplicate connection. Finish required workers before ending the turn.

Use the bounded public `hero` command, not manual gameplay to manufacture proof.
Normal live segments have a 300-second cap, plus separate 60-second setup and
45-second cleanup allowances. Leave the outer timeout long enough for safe
cleanup. The only runtime extension is the exact source-verified Ice Hall
Rescue wait: when the active starter reports that room, the outer monitor may
follow its hard six-hour recovery deadline plus the normal cleanup grace. No
generic sleep, prayer, or live policy may request this extension. Reset retries
and per-invocation segment counts are separate explicit
budgets. A campaign's lifetime `max_segments` limit is optional; an omitted
limit must not stop a long-running HERO campaign at an implicit count.
The Python `run_hero_request` API applies the same cap by default and treats a
missing runtime value as the default; longer runs must be explicit positive
bounded overrides. This keeps non-CLI launchers from creating an unbounded
worker accidentally.
For a self-driving multi-segment run, use `hero --autonomous`. Its supervisor
opens one bounded worker per cycle, carries the same credential and SQLite
checkpoint across cycles, and stops on success, failure, a blocked policy, or
the finite `--max-reset-waits` budget (default three). It never converts an
unchanged reboot or absent source target into an unbounded retry loop. A
`ready` result remains an intentional resume boundary, not proof of progress.
The reset budget counts completed waits; periodic progress messages inside one
wait do not consume additional wait slots.
Ctrl+C is a bounded operator stop: the command exits 130 after the worker's
durable checkpoint is preserved, and the next invocation resumes that
checkpoint. Do not start a second worker while the interrupted process is
still present; inspect the exact process and recover its campaign if required.
Scoped recovery also closes a run row left marked `running` after its linked
campaign segment has already failed, without scanning unrelated run history.

When a deep Moria sanctuary segment reaches its runtime cap at a verified quiet
waypoint, the worker records `campaign_fastwalk_resume_checkpoint` with the
route, boot, room, and stop cursor. The next same-boot invocation may rebuild
only the audited bridge from room 4064 to that waypoint and continue the exact
unfinished leg. Stale boots, malformed cursors, combat, route hazards, and
explicit aborts invalidate the cursor and force the normal source-gated route
selection. If locator narrowing has compacted the live stop list, room 4152 may
be recovered only from the completed source-verified transit stop, with a
positive live large-hobgoblin locator result, a quiet live room, and source
proof that the room is no-mob and has no mobile reset. No other waypoint gets
this fallback. The normal success-return path promotes the starter cursor only
when its explicit `runtime_boundary_requested` flag is true; older saved runs
may use the prior runtime-boundary reason text. Deep-route resume may re-anchor
only on one unambiguous audited transit stop, endpoint, or route leg; ambiguous
room matches remain closed.

Check fresh SQLite events and process state to diagnose silence. JSONL size or
stale metadata alone does not prove a hang. A pre-login socket gets a five-second
banner/creation-prompt bound; an authenticated worker gets the configured
45-second inactivity bound and one bounded reconnect. If it remains silent,
close only that exact worker and preserve interruption evidence. Never kill
unrelated Python or Codex processes. An observation timeout is not proof of
worker exit. If the bounded failure occurred before any command was sent,
checkpoint the segment as `ready` with transport-unavailable evidence; do not
mark a route hazardous, alter XP, or wait for a reboot. If commands were sent,
checkpoint the exact live state as `ready`, add the connection-loss homeward
handoff, and require the next invocation to recover at healer room 3054 before
selecting another route. These resumable transport boundaries stop the current
invocation and never authorize an autonomous retry spin.

## Gameplay And Evidence

### Skill Tree Progression

Review the active pilot's class/subclass skill tree at each level, new practice
balance, observed prerequisite unlock, subclass transition, or relevant source
change. Use a current live listing, source prerequisites and skill code, and
the actual trainer's limits.
Choose useful damage, extra attacks, between-round attacks, disarm, defenses,
and protective/damaging spells; practice their prerequisite chains deliberately.
Set an effective proficiency target, improve high-value abilities toward
mastery where worthwhile, and verify the gain and subsequent unlocks after
each lesson. Preserve physical/intellectual practice budgets, leveling's
unused-practice conversion, stat-training decisions, route safety, and action
registration. An unchanged zero balance or capped teacher is not a reason to
repeat a trainer trip; record the blocker and keep earning current-band XP.

October 13's level-38 audit, before the later Captain visit, had these verified
proficiencies:
enhanced damage **68%**, second attack **64%**, third attack **63%**, armed
combat knowledge **64%**, stun **67%**, and defense knowledge **65%**. The
healer checkpoint then had three physical practices and no intellectual
practices.
The local Midgaard Warrior teacher cannot improve the priority physical skills
under Dorrik's current practice penalty. Source data identifies Cluh'g Mani
(mobile **27205**, room **27616**) as a level-30 teacher with a higher cap; the
current planner predicts useful gains to enhanced damage (**68% to 71%**),
second attack (**64% to 69%**), and third attack (**63% to 68%**). Do not make
that 29-step trip yet: it crosses underwater rooms and needs both flight and
independent water breathing, while source hazard checks still identify the
aggressive rolling calf and Old Higue. Flight alone does not prevent drowning.
Run **17687** then completed a separate source-preflighted route to the live
Warrior Captain in room **30272**. The refreshed practice listing led to one
stun lesson (**67% to 68%**) and two shield-block lessons (**66% to 68%**); all
three physical practices were spent. He returned to healer room **3054** at
full HP with no XP loss. This is the current verified skill state; keep the
Cluh'g Mani route closed until its underwater and hazard gates can be met.
Knight protection-vs-evil/undead remains the next intellectual chain when
Dorrik earns intellectual practices.

At the November 3 healer checkpoint after run **22559**, Dorrik was level **43**
at **1,833,171 XP**, **6,329 XP** from level 44. The level-20 Midgaard teacher
offers no useful lesson for his current priority list, while the source-backed
level-30 Warrior teacher can advance enhanced damage toward **100%**. Prefer
that lowest capable teacher when the fresh listing confirms the local teacher
has no lesson. The route remains optional and unapproved until its independent
water-breathing, source-hazard, resource, and live safety checks pass; a useful
lesson plan is not travel permission. Before the next level, the martial stat
selector should prefer constitution for hitpoint growth unless it is maxed or
measured carrying pressure makes strength more important. If the trainer route
is still blocked, preserve the practices and continue current-band XP.

Run **17664** tested Celia at level 38. Dorrik fled at **177/893 HP** after
his magical armor wore off and Celia was still alive. The flee cost **941 XP**;
damage earned **1,064 XP**, for only **+123 net XP**. He returned to the healer
alive, but the run records a safety loss and no completed kill. Do not
immediately replay this unchanged policy. Keep the priority skill plan active
and prefer another current-band target until a material training, gear, or
protection improvement changes the fight's expected value.

On October 13, the clean DD4 source mirror fast-forwarded from **26749cd** to
**9205f31** and the all-area level-38 candidate scan completed. It ranked the
level-37 Astral Guardian highest, but marked it caution: the source model gives
a **690 damage peak round**, the mobile wields a massive slate-grey sledgehammer,
and the route analysis reports a reachable griffin and Drunk. Treat this as the
next lead to validate, not combat authorization; require fresh exact identity,
route, live consider, protection, and output checks. The same refreshed scan
leaves Celia in caution, consistent with run **17664**'s poor net-XP result.
The upstream changes did not alter `server/src/pre_reqs`, so the recorded
Warrior/Knight practice order remains current. The refreshed `update.c` now
enforces quest points at level gain; Dorrik's **18 QP** do not block level 39,
but he will need **200 QP** before level 50.
Follow-up run **17665** safely closed the Dwarven Catacombs sanctuary route when
the west door remained locked after the source-identified open step; do not
repeat it unchanged. Run **17666** rechecked the Dwarven Ballroom after its
earlier crowd result, found the dancer alone, and earned **2,023 XP** without
loss before returning to the healer. Liquidation run **17667** sold another
dancer's suit for **4 coins** after the prior suit sold for **10**; the amulet
of protection again brought no offer. None of these runs changed Dorrik's
three physical practices or his priority-skill audit.
Run **17668** confirms the low-consider gate: Teacher's last student returned
"no match for you" and was recorded below-band without an attack. The route
then admitted the separate level-34 Yeun Sun Ho on a positive live consider;
Dorrik killed him for **2,190 XP** with no loss. Run **17669** killed the
Dwarven dancer for **2,316 XP** without loss. At the final healer checkpoint,
run **17670**, Dorrik was full, level 38, and **43,563 XP** from level 39, with
all three physical practices intact. Sale pricing is seller-specific: the
Leather Shop paid **4 coins** for a repeat dancer's suit, while the Armourer
paid **42** for another; do not assume one shop's margin applies to another.
Run **17673** confirmed the level gate independently: the chamber attendant's
live consider was "no match for you," so the below-band target was skipped.
Dorrik returned to the healer full with no XP or safety loss. Keep this
level/boot result closed and continue to a different executable policy; his
priority skills and three physical practices remain unchanged.
Run **17674** safely restocked food and water when provisions became a real
shortfall. Run **17675** killed the Dwarven dancer for **1,716 XP** with only
**38 HP** lost, then recovered at the healer. Run **17676** sold the next
dancer's suit for **2 coins** at the Leather Shop; its successive offers were
**10**, **4**, and **2** coins, while the Armourer paid **42** for another.
Dorrik remains level 38 at **1,234,603 XP**, **41,847** from level 39, with
three physical practices.
Run **17677** reached the Freeport warehouse overseer, but live consider said
"no match"; the target was skipped with no XP or safety loss despite the
source estimate. Run **17678** killed the Dwarven dancer for **1,515 XP**;
Dorrik ate the severed arm and sacrificed the corpse for one silver coin before
returning to the healer. Run **17679** sold its suit for **1 coin** at the
Leather Shop. Dorrik finished full at **1,236,118 XP**, **40,332** from level
39; the three physical practices and priority proficiencies remain unchanged.
Run **17680** killed Yeun Sun Ho for **1,713 XP** without loss. Run **17681**
killed the Dwarven dancer for **2,223 XP**, also without loss, bringing Dorrik
to **1,240,054 XP**, **36,396** from level 39. Run **17682** safely sold loot
and returned him to the healer. The next bounded campaign attempt, run **17683**,
quoted **141 copper** for a light-blue travel potion, bought and quaffed it,
verified its flight objective, and received the healer's farewell on logout.
That supply segment added no XP or loss; it provides fresh evidence that this
reboot's shop quote was affordable, not a fixed price guarantee. The campaign
was then checkpointed at the healer, level 38, with three physical practices.
Run **17684** reached the Lotus Temple but the live `consider` for Yeun Sun Ho
said “no match,” so Dorrik skipped that instance, recalled, and finished safely
without XP change. This contrasts with the earlier positive Yeun kill: judge
each live instance rather than allowing a source/name match to authorize it.
Run **17685** passed its own live gates and killed the Dwarven dancer for
**2,207 XP**; Dorrik recalled at **490/893 HP**, above the configured 20% floor,
and recovered at the healer without XP loss. Run **17686** safely sold loot.
Run **17687** used the three available physical practices at the live Captain
trainer as recorded above, then saved and quit safely at the healer. Run
**17688** safely confirmed the healer checkpoint. Run **17689** followed eight
bounded live `where citizen` relocations through the mapped Isle of Quake
rooms, but never observed a citizen at a reached endpoint; it returned safely
with `objective=not_achieved`, no kill, and no XP loss. The locator ledger
records eight attempts, not a proven target absence; do not blindly repeat the
same circuit without changed live location evidence. Run **17690** then
received a positive live consider on the Dwarven dancer, landed stun at **68%**,
and killed her for **1,531 XP** without loss. Its fresh campaign training audit
confirmed stun **68%**, shield block **68%**, and zero physical/intellectual
practices. The current campaign checkpoint **51866** is level 38 at
**1,243,792 XP**, **32,658** from level 39; other priority proficiencies remain
at their previous verified values.
Run **17691** safely sold loot. Run **17692** reached the Shrine Attendant's
registered endpoint but found no target, then returned safely without XP
change. Run **17693** passed fresh live identity and consider checks, landed
stun at **68%**, and killed the Dwarven dancer for **1,802 XP**. Dorrik finished
safely at healer room **3054**, with no XP loss. The latest checkpoint **51873**
is level 38 at **1,245,594 XP**, **30,856** from level 39. Its training audit
still shows zero practices, stun **68%**, and shield block **68%**; keep using
the trained stun in admitted fights and resume skill-tree review promptly when
a level, practice gain, or unlock changes lesson eligibility.
The next bounded campaign pass safely liquidated loot (run **17694**), bought
and verified flight from a fresh affordable shop quote (run **17695**), then
completed another source-ranked Dwarven dancer kill for **1,790 XP** (run
**17696**). Its transcript confirms the exact target passed live consider and
logout was confirmed. Checkpoint **51878** is level 38 at **1,247,384 XP**,
**29,066** from level 39. The fresh training listing remains unchanged with
zero practices, so continue using stun and do not make an empty-balance trainer
trip.
Runs **17697–17699** added no XP. The Quake candidate in room **12194** was
not reached: at Midgaard, three fresh `where drunk` checks still showed the
greeter at **Alley at Levee** and **the Pet Shop**, so departure stopped safely
before travel. Keep that exact route closed until fresh locator evidence
changes. The later Dwarven Ballroom check saw the dancer with a maid in the
room; the isolation gate marked it crowded and skipped combat. Do not retry
either unchanged condition. Checkpoint **51885** remains level 38 at
**1,247,384 XP**, **29,066** from level 39; the fresh skill audit still shows
zero practices, stun **68%**, and shield block **68%**.
A fresh all-area candidate scan ranks the level-**37** Astral Guardian in room
**1906** as the next lead: its short registered route requires flight, and the
source model estimates a **690-damage peak round** because it wields a
massive slate-grey sledgehammer. A reachable griffin and the Drunk are route
hazards. Keep this as a caution candidate, not an automatic rejection; require
fresh live route and target identity, positive consider, flight, and the normal
20% survival/output gates before deciding whether to fight.
Run **17700** checked the source-ranked sanctuary-reserve Alchemist at room
**927**, but live evidence confirmed the target absent; no sanctuary objective
or XP was achieved. Run **17701** likewise found the Shrine Attendant absent at
room **10822** and returned safely. Run **17702** then found the Dwarven dancer
alone, passed live consider, opened with stun at **68%**, and killed her for
**2,397 XP** using six Flamestrikes at **48%**. No combat loss was recorded;
the post-fight healer score was **724/911 HP**. Checkpoint **51890** is level 38
at **1,249,781 XP**, **26,669** from level 39. The fresh training listing still
shows zero practices, stun **68%**, Flamestrike **48%**, and kick **68%**.
The transcript showed kick was not used because the source-spell branch always
preempted repeatable actions. The combat loop now alternates the admitted
source-planned spell with an eligible repeatable attack, while preserving
capability and target gates; a focused sequence test is added. Syntax checking
passed; the daily regression-test allowance was already used, so the new test
has not yet been run.
Run **17703** could not liquidate loot: three bounded `where drunk` checks
still blocked the Midgaard shop route, so it stopped safely before sale. Run
**17704** then live-verified the new skill rhythm: stun, Flamestrike, kick,
Flamestrike, kick, Flamestrike. The dancer died for **2,259 XP**; Dorrik slept
at the Healer and recovered from **665/911 HP** to full without XP loss. Run
**17705** found the dancer absent at room **20516** and returned safely without
combat. Checkpoint **51897** is level 38 at **1,252,040 XP**, **24,410** from
level 39. The fresh audit remains at zero practices, with kick **68%** and
Flamestrike **48%**. Do not repeat the absent target without changed evidence.
Runs **17706** and **17708** each deferred loot liquidation safely after three
bounded checks found the source-backed Drunk blocking the city shop route. In
run **17708**, `where drunk` first returned Weapon Shop, Poor Alley, and Practice
Yard, then Main Street, Poor Alley, and Practice Yard; the route remained
blocked. Do not retry that sale route until fresh evidence makes a registered
route clear. Between them, run **17707** bought a light-blue flight potion for
the fresh quoted price of **141 copper**; `affect` confirmed `fly` for **34 MUD
hours**. The purchase succeeded but added no XP. Checkpoint **51900** remains
level 38 at **1,252,040 XP**, **24,410** from level 39, with no practices
available and no XP loss.

The October 12 level-37 audit (run **17560**) found Dorrik had no physical or
intellectual practices to spend. His useful combat skills included enhanced
damage **68%**, second attack **64%**, third attack **63%**, stun **67%**, kick
**68%**, Flamestrike **48%**, and healing magiks **52%**. Keep earning current-
band XP until practices or unlocks change; do not make an empty-balance trainer
trip. The next source-backed Warrior skill-tree target is disarm: its
prerequisites are Warrior **30%**, grip **85%**, and defense group **85%**.
Dorrik already has grip **99%** and defense knowledge **65%**; at the next
physical practice balance, refresh the live learnable list and teacher limits,
then test whether raising the defense-group path toward **85%** unlocks
disarm. Verify every lesson and unlock live. Keep comparing that path with
enhanced damage, attack-chain gains, and the Knight protection/spell chain;
source value alone never proves current trainer access.

On October 13 NZST, run **17720** refreshed Dorrik's level-38 skill listing at
healer room **3054**: enhanced damage **68%**, second attack **64%**, third
attack **63%**, stun **68%**, defense knowledge **65%**, grip **99%**, dodge
**66%**, and no physical or intellectual practices. The learnable entries
(conjuration magiks, inner force, rescue, riding techniques, and swim) were all
at **0%**. No lesson was actionable, so continue current-band XP rather than
making an empty-balance trainer trip. Recheck at the next level, practice gain,
unlock, or relevant source change; keep disarm's defense prerequisite on the
priority list once a useful practice becomes available.

October 10 runs **16891**, **16920**, and **16921** confirmed Dorrik's level-32
live `practice` listing:
enhanced damage **67%**, kick **67%**, stun **62%**, second and third attack
**63%**; `flamestrike` and `healing magiks` appeared as learnable at **0%**.
Physical and intellectual practice balances were both **zero**, so no lesson
could be taken. Run **16921** showed no proficiency change. A planner-only
check against that exact live listing, with one hypothetical practice per
type, selects `flamestrike` **0% to 45%** (intellectual) and `enhanced damage`
**67% to 100%** (physical). This does not prove teacher capacity or authorize a
lesson; recheck the actual teacher's positive gain before dispatch. Third attack
already meets its analysis target of **60%**.
Source analysis prioritizes Knight protection wards, flamestrike, and the healing
chain, but the wards were absent from this live learnable list; do not infer
trainer access or practice a lesson until fresh eligibility and capacity checks
pass. Reuse this audit until level, practice balance, unlock, subclass, or source
changes.

October 11 run **17073** refreshed Dorrik's level-33 listing at healer room
3054, then verified the nearby Cleric guildmaster accepted two practices:
`flamestrike` rose from **0%** to **27%**, then **41%**. The final listing
showed **zero** physical and intellectual practices and `healing magiks` still
learnable at **0%**. The next useful target remains `flamestrike` **45%**;
the current blocker is no intellectual practice, not trainer access. Recheck
the tree when a new practice is earned, continue that chain if still eligible,
and then reassess the healing/protection unlocks before spending further.

Run **17079** used the one-use source-output revalidation for the dwarven
musician but ended `objective=not_achieved`, `safety=loss`; Dorrik withdrew at
the 20% floor and returned to the healer. The trace shows the source budget
credited Flamestrike while the live action selector issued stun, kill, then 17
kicks and no Flamestrike. The controller now gives an exact, practised,
affordable source-planned spell priority over other repeatable attacks after
disarm, subclass setup, and control actions. The planned spell keeps the normal
mana reserve check. Its focused command-selection test is deferred because
today's regression allowance has already been used; this is not yet live proof,
and run 17079's target remains closed after its recorded loss.

October 11 runs **17130** and **17131** refreshed Dorrik's level-34 live skill
audit. Current proficiencies include enhanced damage **67%**, second attack
**64%**, third attack **63%**, kick **67%**, stun **66%**, armed combat
knowledge **64%**, defense knowledge **65%**, grip **99%**, and Flamestrike
**48%**. The observed learnable listing showed conjuration magiks, inner force,
rescue, riding techniques, and swim at **0%**; both physical and intellectual
practice balances were **zero**. Source analysis keeps enhanced damage on the
path toward **100%** and prioritizes attack-chain improvements and the
prerequisites for disarm as they become available. No lesson is currently
actionable; the immediate blocker is practice availability, and the exact
teacher's positive gain must still be verified before any training trip. Recheck
at the next level, practice gain, unlock, subclass, or source change; keep
current-band XP moving while the balance is empty.

October 11 runs **17143**, **17146**, and **17148** verified the Knight combat
sequence in live fights: consider, stun with the hammer, switch back to the
long sword, then use practiced Flamestrike between rounds. Those targets were
killed for **1,146**, **1,610**, and **1,792 XP** without an XP loss. Run
**17150** reconfirmed the level-34 skill listing and zero physical and
intellectual practices; its separate Quake target produced **1,870 XP** with
Flamestrike in the rotation. There is still no lesson to take. Continue current-
band hunts, then recheck the tree immediately on a level or practice change and
advance enhanced damage toward mastery alongside newly unlocked class skills.

October 11 run **17229** observed Dorrik at level 35 with enhanced damage
**67%**, armed combat knowledge **64%**, third attack **63%**, Flamestrike
**48%**, healing magiks **49%**, **3 physical** practices and **0
intellectual** practices. The latest saved run is **17230**, checkpoint
**50877**, at healer room **3054**. The current DD4 source revision is
`4c039fa6b0f84d51ae7d40e516977fbb8ebc6ad3`.

The Knight source requires `protect vs evil` **60%** to unlock `protect vs
undead`; the former training target incorrectly stopped at **50%**. Its target
is now **60%**, tied to the current prerequisite snapshot and covered by a
focused test. The changed training-policy fingerprint will force a fresh
campaign training audit. Neither ward appeared in the observed live learnable
listing, so live teacher support remains unproved.

Source teacher checks found no safe nearby trainer that can currently raise
enhanced damage: the level-20 Warrior teacher caps the skill at **80%**, which
cannot improve Dorrik's **67%** with his observed practice penalty. Level-25,
-30, and -35 teachers have more capacity, but their routes fail current source
hazard checks; the level-35 teacher at room **31077** would raise it to **75%**
on the next practice, but its 115-step route crosses the Barracuda reset in room
**10005** and a `spec_thief`. Strict safe-route search found no alternate.
Preserve the unused practices, do not repeat an unchanged teacher audit, and
continue executable level-35 XP policies until practice, stats, or route
evidence changes.

Run **17231** superseded that unused-practice snapshot: the live level-35
listing showed three physical practices, stun **66%**, and shield block
**62%**. At the Captain in Kerofk, one accepted lesson raised stun to **67%**;
two raised shield block to **65%** and then **66%**. The final practice count
was zero. These are verified improvements, not mastery: on the next earned
practice, refresh the full class tree and teacher limits, then favor the
highest-value reachable leveling skill rather than repeating these lessons by
habit. Run **17276** later confirmed Dorrik remains level 35 with **986,559 XP**
and no practices; keep the skill plan current while continuing XP progression.

Run **17310** advanced Dorrik to level 36 at **1,011,355 XP** and awarded
three practices. The immediate post-level run **17311** refreshed his skill
listing at the Cleric's Inner Sanctum: **3 physical, 2 intellectual**. The
guildmaster accepted two intellectual lessons, raising healing magiks from
**49% to 52%** and learning cure light at **28%**; the final balance was **3
physical, 0 intellectual**. On the next selection, use a fresh class-tree and
teacher-capacity audit to find a source-safe instructor for the physical
points. Enhanced damage remains **67%** and a high-value priority toward
mastery; also weigh the attack chain, stun, and disarm prerequisites against
the exact teacher's proven gains. Do not spend physical practices merely to
empty the balance.

Run **17313** performed that fresh level-36 audit at the Captain in Kerofk.
The reachable teacher used Dorrik's three physical practices on dodge, raising
it from **60% to 66%**; enhanced damage remained **67%**, and no practices
remain. This is a verified defensive improvement, not a reason to repeat the
same trainer visit. Continue level-36 XP progression and refresh the skill
tree at the next level, practice gain, unlock, or relevant source change; keep
enhanced damage and the attack chain ahead of lower-value options whenever a
safe teacher can actually improve them. The same run killed the dwarven dancer
for **3,242 XP**, recovered a dancer's suit, and returned safely to healer room
**3054** without XP loss. Dorrik ended at **1,014,597 XP**, **79,253 XP** from
level 37.

Run **17314** then verified the level-36 Lotus Temple route live: Dorrik
stunned Yeun Sun Ho, used Flamestrike between attacks, and killed him for
**2,742 XP**. He recalled and recovered at the healer with
`objective=achieved` and `safety=safe`; the refreshed skill audit still shows
enhanced damage **67%**, dodge **66%**, and zero practices. Continue XP
progression, then reassess the class tree immediately when new practices or
unlocks appear. Run **17318** repeated the source-ranked dancer hunt and
produced another **3,120 XP**, ending at **1,020,459 XP** with
`objective=achieved` and `safety=safe`. The same training blocker remains: no
practices are available, so continue XP progression rather than repeating the
unchanged trainer visit.
Run **17320** repeated the Lotus Temple kill and earned **2,905 XP**, ending
at **1,023,364 XP** with `objective=achieved` and `safety=safe`. The fresh
audit remains at enhanced damage **67%**, dodge **66%**, and zero practices;
continue current-band XP and recheck training on the next unlock or practice
gain. Run **17322** completed another safe dancer kill for **2,417 XP**, taking
Dorrik to **1,025,781 XP**. No new practice points or skill unlocks appeared;
the training priorities remain unchanged until the next level or practice
change. Run **17324** added **3,101 XP** from another clean Yeun Sun Ho kill,
bringing the total to **1,028,882 XP** with no XP loss. Enhanced damage remains
**67%**, dodge **66%**, and the practice balances are still empty.
Runs **17316**, **17321**, **17326**, and **17331** each found Celia (mobile
**30244**) at room **30291**, but the live crowd check counted two observed
mobiles and declined combat. All four were safe, not achieved, and produced no
XP. Keep this exact stop closed until fresh live evidence changes the room
count or target location; do not force another unchanged trip. Run **17327** then
completed a two-kill Dwarven Home circuit: the dancer paid **2,382 XP** and a
route musician paid **1,855 XP**, for **4,237 XP** total. Both were looted and
Dorrik returned safely at **1,033,119 XP**. The skill audit remains unchanged
with no practices available. Run **17332** selected Teacher's last student,
which failed live consideration; the route continued to Yeun Sun Ho and earned
**2,302 XP**. Record `safety=safe` separately from
`objective=not_achieved`, since the selected target was not killed. Dorrik ended
at **1,035,421 XP**, still level 36 with no practices.
Run **17334** demonstrates the cost of extending the circuit after its first
kill. Dorrik earned **2,136 XP** from the dwarven musician, then attacked a
1,449-HP dancer after consider said “perfect match” but “built like a tank.”
At **87/844 HP** he fled; DD4 charged **830 XP** and awarded **733** damage XP
for the escape, leaving net progress **+2,039 XP** at **1,037,460 XP**. The run
is `objective=not_achieved`, `safety=loss`; Dorrik survived and reached the
healer. Keep the exact failed dancer encounter closed unless fresh source or
live evidence changes its output/survival case. The skill audit remains
enhanced damage **67%**, dodge **66%**, and zero practices.

Run **17337** started after the source mirror advanced from **4c039fa** to
**26749cd**. Startup cleared Celia's same-boot crowd result and cooldown, so
selection sent Dorrik back toward that policy. Before departure, `where drunk`
reported the Drunk at Temple Square and the Practice Yard; three bounded waits
did not clear the route. Dorrik saved and quit safely at healer room **3054**,
with no target contact, combat, XP change, or loss. This exposed two persistence
gaps: a source refresh must retain exact same-boot crowd evidence, and a later
no-travel city block cannot supersede a crowd observation at the target room.
Both repairs and focused tests are now in the worktree; the October 11 test
allowance was already spent, so the new cases await the next daily batch.

Run **17338** confirmed both source-registered Kerofk Bartender locations were
below-band at level 36: live `consider` returned “The Bartender is no match for
you” in rooms **30246** and **30265**. No attack was issued. Dorrik returned to
healer room **3054** at **1,037,460 XP**, with full HP and movement and no loss.
Both exact policy/room sightings are saved as same-boot below-band evidence;
select a different current-band candidate rather than repeating either room.

Run **17339** tested the Freeport source-ranked circuit. Live `consider`
returned “The harbormaster is no match for you” in room **29116**, so Dorrik
did not attack him; the route's warehouse overseer in room **29129** passed
the fresh combat gates and was killed for **2,286 XP**. The segment reached its
runtime boundary, returned Dorrik to healer room **3054**, and completed a safe
save/logout with no XP loss. Final state: level **36**, **1,039,746 XP**,
**54,104 XP** to level 37, **854/862 HP**, and **441/596 movement**. The skill
audit still shows enhanced damage **67%**, dodge **66%**, and zero practices.

Run **17340** was a bounded healer setup, not progression: Dorrik restored
movement, changed from recovery gear to combat gear, checked his potion pouch,
saved, and received a confirmed farewell. Run **17341** then attempted loot
sales, but three fresh `where drunk` checks after bounded healer sleeps kept
reporting the wandering Drunk at Temple Square and Alley at Levee. No sale or
XP change occurred; the saved character remained alive at healer room **3054**
with full HP and movement. The liquidation route is closed on this evidence;
do not repeat its waits without a changed locator result. Its transcript has no
explicit `quit` acknowledgement, so verify connection status on the next
bounded login rather than assuming the logout was confirmed.

Run **17342** completed the bounded Magic Shop support purchase safely. The
live quote was **141 copper-equivalent**; Dorrik bought and quaffed one light
blue potion, and `affects` confirmed flight. He returned to healer room **3054**
and received a confirmed farewell. XP remained **1,039,746**. On the next login,
recheck `affects` rather than assuming the potion's flight duration survived
logout; keep using live prices instead of a fixed reboot-independent cost.
Run **17343** rechecked the liquidation route after a fresh locator and used the
Jeweller in room **3034**. The live `value notebook` offer was zero; Dorrik
donated the redundant notebook rather than treating the route as a funding
success. He saved and received a confirmed farewell at the healer, with no
currency or XP gain. The exact notebook/Jeweller zero-offer pair is recorded;
do not repeat it unless the item or shop evidence changes.
Run **17344** selected the source-ranked Kaladim hunt for “a large knife,” but
the audited route required live invisibility to cross its source-known
aggression. Dorrik has no learned, usable invisibility spell or verified
substitute; the safe-origin preflight therefore returned him to healer room
**3054** before field departure. He saved and logged out safely with no combat,
XP change, or loss. The same live `practice` audit confirmed zero physical and
intellectual practices. Keep this route closed until its invisibility gate can
actually be met; do not spend another cycle rediscovering the same blocker.
Run **17345** returned to the Lotus Temple route after the source audit
confirmed its level-18 small green lizard cannot join the level-36 fight.
Fresh live evidence found Yeun Sun Ho, `consider` admitted him, and the bot
recorded a confirmed kill for **1,836 XP**. Dorrik finished without loss,
recovered and logged out safely at healer room **3054**: **1,041,582 XP**,
**52,268 XP** to level 37, and **862/862 HP**. The skill audit remained
enhanced damage **67%**, dodge **66%**, with zero practices; refresh it after
the next practice gain or level transition.
The currency snapshot rose from **1** to **2 silver** across run **17345** with
no shop sale in that segment, a likely coin source from the encounter; keep it
as a live observation, not a general drop guarantee. Run **17346** found no
eligible sale candidate and completed a short save/logout at the healer with
no further XP or currency change. Do not repeat that empty liquidation check.
Run **17347** spent **177.6 seconds** reaching the Lotus Temple chamber
attendant; exact live `consider` returned “Chamber attendant is no match for
you.” No attack was issued. Dorrik returned and logged out safely at healer
room **3054**, full on HP, mana, and movement, with no XP change or loss. Keep
the exact room/target closed as same-boot below-band evidence and prefer a
different current-band policy over repeating this long route.
Run **17348** then found Yeun Sun Ho again on a fresh live route and passed a
new `consider`. The hammer stun landed (“causing him to buckle and collapse”);
Dorrik switched back to his primary and confirmed the kill for **1,390 XP**.
The **184.7-second** run finished without loss or combat timeout and logged out
safely at healer room **3054**. Currency rose by one silver (**2** to **3**)
without a shop sale, a second encounter-level coin observation. Final progress
is **1,042,972 XP**, **50,878 XP** to level 37. The skill audit remains
enhanced damage **67%**, dodge **66%**, with zero practices.

Run **17187** reached Yeun Sun Ho in room 10771 but ended without considering
the level-34 target: the crowd gate treated its level-18 small green lizard
companion's `spec_poison` as an active threat. `special.c:2530-2547` shows
`spec_poison` only bites a character already fighting that lizard, and the
source level window proves this lizard cannot join Dorrik's fight. The room
hazard check now consults the existing source-backed non-assisting proof before
blocking combat-only specials, while retaining guard and joinable-poisoner
hazards. A focused regression case covers below-band versus joinable poisoners;
it has not been run because today's regression batch was already used, and this
route still needs live proof before being treated as productive.

Run **17188** is a live calibration: Dorrik considered the source-ranked
Gambler at two Kerofk rooms and DD4 returned “The Gambler is no match for you”
both times. `act_info.c` computes `diff = victim->level - ch->level`; this
message is the `diff <= -5` branch, so no attack was issued and the exact
candidate is now below-band evidence for this level and boot. Its source level
is 28, but the live load landed at least five levels below Dorrik. Preserve the
negative result rather than reopening the same target without changed evidence.

Keep three run outcomes separate: execution says whether the bounded worker
finished its procedure, objective says whether the stated goal is proved, and
safety records deaths or losses. A safe abort may be `execution=success` and
`safety=safe` while the objective is `not_achieved`. Do not infer success from
a default level value for maintenance work or reuse a stored positive objective
claim when current evidence is unknown. Quest reward requires an observed
positive quest-point delta; level transition is a separate explicit condition.
Required-item objectives must be recorded in run context and matched to
distinct acquired or carried entries. Older campaign summaries may supply
cached time/progress metrics, but their positive objective claims remain
`unknown` until a bounded summary refresh verifies them.

Midgaard recovery and logout belong at healer room 3054, one north of recall,
not the Mage's Laboratory. Wake to eat/drink during sleep when needed; never
change equipment asleep. Never log out in Purgatory: recover the corpse, loot,
restore gear, leave the portal, then hand off once to healer recovery.

Checkpoint 57331 confirms this recovery path live. After the unsafe arena run
18924, run 18925 exposed a crawler stall: it kept issuing `look` at room 401
after returning from room 410 even though room 410 still had unvisited exits.
The crawler now stores each room's observed exits, reuses a parent edge only
when that parent has remaining work, and ends with a bounded failure instead of
repeating `look`. Run 18926 then found and looted Dorrik's corpse, entered the
portal, restored gear, slept at healer room 3054, and logged out safely. This
is recovery evidence, not XP or HERO completion.

Checkpoint 57349 records the next safe selection boundary: run 18927 earned
330 net XP from a Kaladim black bat, run 18928 closed a duplicate attempt
without a kill, and run 18929 bought a flight potion. The current source audit
has no plain-executable candidate while the Sanctuary recovery route waits for
its area reset. `spec_cast_psionicist` remains a hard gate: energy drain begins
at source level 14 and disintegrate at 35, so a level-40+ psionic is excluded
unless a fresh disintegration-protection receipt is present. Sanctuary alone,
Globe, energy containment, Illithid resistance, and item lore do not qualify.

For urgent source-food routes, wake from healer sleep only to use carried food
or water, or when the registered route's movement threshold is met. If starving
without supplies and still below that threshold, keep sleeping until the route
is affordable; do not alternate stand/sleep at unchanged movement or depart
below the registered budget. This avoids waiting for HP recovery while
starving without stranding the character in a no-progress loop.

On DD4, an invisibility affect at duration 0 can still be active until the next
30-second affect update, and `spell_invis` rejects a recast while that affect
remains. For a source-registered visibility route starting at recall, do not
cast or travel on a duration below 2: go north to room 3054, sleep, and check
at most twice at 30-second intervals. Once GMCP removes the affect, wake, return
south to recall, and cast again. If it remains after the bounded checks, stop
at the healer; never enter the route without fresh observed invisibility.

Optional loot-sale trips must use a fresh live `where drunk` check, even when
the source-bounded city-transit exception is otherwise available. A shop visit
does not justify accepting a greet attack: the cityguard may join the drunk's
fight, turning a small kill into a costly withdrawal. A source estimate or an
older route clearance is not a substitute for the live check.

Field recall is an asynchronous command: keep it in flight until a real
Temple-of-Midgaard room response or equivalent authoritative room update is
observed. The runner may use the decision-time `CharacterState` room as the
recall origin when the text parser is one event batch behind; a missing
immediate response is not an immediate recall failure. The normal bounded
inactivity and reconnect watchdogs still apply.

If a flee fails during a recallable emergency, try fleeing once more when the
character is still at least half healthy and an enemy is still present. This
single retry avoids paying an unnecessary recall penalty while combat is still
active. Poison, low health, no-recall rooms, and a second failed flee use the
existing direct-return path instead; never spin on repeated escape attempts.

After a successful emergency flee, perform one bounded room audit. If a
pursuer remains, an ordinary hunt must use the direct audited return rather
than issuing another flee. Consider-only research and required-loot routes may
use one explicitly bounded second flee before returning. The follow-up must
then hand off to the normal return controller; it must never restart the
post-flee audit cycle or repeatedly charge the level-scaled flee penalty.

Optimize useful kills and net XP per complete journey. Keep attacking viable
targets until a meaningful health, protection, nutrition, movement, or runtime
boundary. Do not kill below-band targets for XP, infer emptiness from one room,
or treat sanctuary expiry alone as a losing fight. An exact source-required
resource or loot target may be admitted below-band only with positive carrier
evidence, a bounded safe route, and an explicit missing-resource objective; its
XP is maintenance evidence, never progression evidence. Retain source risk,
crowd, consider, and observed loss gates. Repeated attempts need changed
evidence.

Continue pursuing eligible current-band XP regardless of how recently the MUD
rebooted. A reboot can improve a particular target's XP or refresh a reset-based
resource, but it is never a general reason to pause hunting. Wait only for a
specific reset-dependent objective; if that route is cooling down or exhausted,
choose another worthwhile policy that passes the same live safety gates.

When an urgent source-ranked food run starts with no carried food, the planner
may chain a distinct, same-area source food reset when the complete route still
fits the movement budget and both legs pass the normal source and live-navigation
gates. Keep every required food item in the pending-reserve check, including
earlier stops after the field cursor advances. Do not consume the first item
while a later stop is outstanding; after one item is eaten, retain any remaining
source-verified food for the next recovery window.

Source-ranked routes may carry one source-validated borderline transit
aggressor whose maximum fuzzy level is exactly four below the character. The
route must register that mobile's exact source VNUM, and the live encounter
must still be one isolated GMCP identity at or below the useful-XP floor with
normal health, nutrition, consideration, and combat gates satisfied. Finish
that single defensive interruption through the existing bounded transit-fight
state machine, record it as maintenance, and then resume or return according
to the route contract. A same-room crowd of source-known below-band mobiles is
rejected before combat; do not fight one member and flee the rest. Fixed routes,
unregistered VNUMs, crowds, specials, programs, or useful-band live rolls remain
withdrawal conditions.

An ordinary source-ranked endpoint may be admitted behind a route containing
only source-identified, strictly below-band aggressors when every one passes
the existing bounded damage/equipment proof. The endpoint itself must be
passive, special-free, script-free, source-identifiable, and in the current
source band; the route must have no hard hazard or attack-program preflight.
These transit mobiles are maintenance interruptions, never XP targets. The
live runner still requires exact GMCP identity, one-mobile isolation, normal
consider and health-floor checks, and the finite transit-fight/return rules.
The Goblin Fortress visitor probe on 2026-10-20 (run 18966, guard VNUM 20315)
failed that live health boundary and is closed for the current reboot. This
exception never applies to `spec_cast_psionicist`; energy drain and
disintegrate remain hard protection gates.

The live deployment currently predates the Goblin Fortress template conversion.
For the ordinary Goblin Visitor (mobile VNUM 20301), use the audited legacy
prototype from source revision `e48256a59aa326cd99fe6669dddf896d690bcade`
until a live probe proves that deployment has caught up. The current upstream
template record is research-only for this mobile: it does not prove the live
flags or scalar damage metadata. A source-metadata revalidation may reopen one
old unresolved no-connection result after that legacy overlay is applied, but
the normal live identity, isolation, consideration, health, route, and combat
gates still decide whether the visitor can be engaged.

A world-time probe may recheck a recorded city-shop obstruction once from healer
3054. Only a complete, positive off-route locator from that successful run,
with the same observed reboot, can release route cooldowns. Missing or absent
locations, cached checkpoint evidence, and actual purchase failures cannot do
so. This supersedes kill-only aging for that positive revalidation case, not
the normal shop preflight or any combat-loss gate. No additional wait, segment,
loan, or purchase is authorized by the probe.

During loot liquidation, if the locator blocks one planned buyer but another
already-planned compatible buyer has a route that avoids every observed hazard
room, defer only the blocked entries and complete the safe sales. The hazard
and its cooldown remain evidence for later retry; this does not authorize a
new shop route, clear a live obstruction, or turn unsold equipment into XP.

If a compatible shop returns DD4's generic uninterested response, preserve the
refusal and try at most one other source-compatible safe buyer, excluding every
shop already attempted for that item. This distinguishes a shop-specific
refusal from a zero-value or otherwise unsellable object without creating a
shop loop. If the alternate also refuses, record no proceeds and donate or
sacrifice the item according to the normal release rules.

The same rule applies to a field-city departure that stopped after its bounded
healer waits. Persist `campaign_field_city_preflight` with its level, reboot,
locations, stop evidence, and exact policy ID. A same-level, same-reboot
continuation cools down that exact route while another source-ranked route may
run its own bounded preflight. Legacy checkpoints without a policy ID do not
close the whole source frontier: the selected candidate may make one normal
preflight, and its policy ID is saved before the live segment so an interrupted
attempt cannot blindly reconnect to that route. Confirmed blocks accumulate in
a level- and reboot-scoped policy ledger, surviving healer recovery without
reopening earlier failed routes. A level change or reboot expires that ledger.
The route check still grants no permission to cross a live hazard or engage a
target; all existing movement, health, transit, and combat gates remain active.

If a live `where drunk` result blocks only the Midgaard prefix of a
healer-origin hunt route, the runner may try one source-mapped detour to the
same first outside-city waypoint. This applies both when the healer departure
check finds the Drunk and when a fresh route-level locator at room 3001 finds
it, even if no separate healer-side preflight ran. Every reported room name must
map to the Midgaard source map; the detour must avoid those rooms, add no more
than 16 commands, pass source hazard checks except for the exact bounded drunk,
and leave enough movement for the revised route plus its 15-point reserve. The
player must be at least 95% healthy. Unknown locations, a matching location
later on the target route, custom return commands, or any other hazard refuse
the detour. The runner then repeats `where drunk` on the revised route before
moving; a continued obstruction uses the ordinary bounded waits and cooldown.
If the revised healer-side route is newly blocked by a changed location set, or
a fresh `where drunk` at safe recall room 3001 reports a different Midgaard
location set on the route prefix, allow one separate corrective detour from the
new live evidence. Preserve both location sets and detour records, require the
same source mapping, hazard, health, and movement gates, and repeat the locator
before departure. No third detour is allowed; a still-blocked route returns
safely and is checkpointed unavailable.
If the exact source-ranked policy is otherwise the only executable current-band
candidate, one persisted revalidation may reopen it once. Arm only from the
same-level, same-boot, same-source-revision successful no-travel segment when
the saved evidence contains the first mapped detour, a changed later locator,
unchanged XP and movement, no loss, and no attempted correction. Consume the
marker before starting a new segment, reconstruct the first detour from the
current source map, and require its evidence to match exactly before passing it
to the runner. The runner must query live locations again and use the existing
health, movement, source-hazard, and correction checks. A reconstruction
mismatch, other live hazard, or second attempt stays closed; this does not
clear other cooldowns or grant combat permission.
There is one separate full-route case for an exact source-ranked policy whose
healer departure was blocked before any outbound movement. It may be reopened
once only after ordinary current-band selection finds no executable target, at
a living healer checkpoint at least 95% healthy, and only when a later
same-level, same-boot, same-source-revision locator is complete, unblocked,
and reports a changed location set. Prove that observation from a bounded
successful segment whose start/end locator sets differ and whose level, boot,
source revision, XP, loss, and kill evidence remain unchanged. The locator's
run ID must match its segment row; legacy records without one need changed
start/end location sets. The earlier successful segment
must show three bounded waits, `outbound_index=0`, unchanged XP and loss totals,
and no completed or objective kills. Map every earlier location name to Midgaard
source rooms, require the original shortest route to cross one, and register
only an alternate source route that avoids all of them and adds 21 or 22
commands. Keep the old city-blocked policy ledger intact and persist a separate
one-use marker. Re-rank only that exact policy; consume the marker before its
segment and require a fresh live locator plus all normal route, health,
movement, source-output, protection, consider, and combat gates. Any mismatch,
new obstruction, unavailable route, or second attempt closes the exception;
it never clears cooldowns or grants combat permission.
If a source refresh intervenes, allow one distinct refresh revalidation only
when the earlier blocked segment and later changed, unblocked locator were
both recorded under the same prior revision, and the current-source candidate
still has the exact policy, mobile VNUM, room, and route. If the blocked
segment fell outside the normal eight-row tail, fetch only that policy's
latest segment with the bounded 256-row lookup; never expand checkpoint
history. Persist this separately as
`campaign_field_city_source_refresh_revalidation`; retain the old route marker
and blocked-policy ledger unchanged. Match the locator to its exact successful
segment/run in the bounded recent history. The fresh live locator and every
normal gate still apply.
The same source-refresh marker may carry `route_clear_recheck` when the old
blocked and later clear locator segments share their prior source revision and
the current-source candidate retains the identical route. Map every old and new
city label to rooms; require the old blocker on that route and all later
locations outside it. This reopens only the exact route for one fresh live
preflight; preserve the earlier clear-route marker and blocked-policy ledger.
Release that closure only after a linked positive-XP kill and safe healer return.
A city-blocked policy must not short-circuit offline source selection: keep
that exact policy excluded unless its one-use marker is pending or its exact
route-clear recheck has verified productive completion, but allow
other current-band candidates to pass their normal source and route gates.

There is one distinct unchanged-route recheck when a wandering city blocker
has moved completely off the route. After ordinary current-band selection and
the existing detour rechecks find nothing executable, require a recovered
healer checkpoint, one plain unarmed candidate passing every independent
current-band, useful-XP, output, protection, flight, and target-loss gate, and
a later successful run-linked locator with complete changed location evidence.
The campaign can obtain that observation itself: after ordinary selection
closes, a linked successful safe no-travel city stop with three waits may
receive one `campaign_field_city_observation`. Require the same current
source, level, boot, XP, loss, and recovered healer boundaries. Persist it
before dispatch, use the ordinary world-time worker with the exact saved city
route labels, keep reading through at most three 12-second waits, and save/quit
at healer 3054. No outbound command or attack is permitted. A complete clear
locator is a next-segment handoff, not an area-reset wait or XP progress.
Failure or continued obstruction consumes the observation and stops.
The existing clear-route marker may cover a source-proved small plain
population. Require its full reset audit and ordinary no-reserve output proof,
plus independently measured same-boot useful-kill history after the fresh-search
cap. A no-travel city stop must not erase that historical reward, while weak
individual receipts remain recorded and every new target still gets fresh
isolation/consider. Only the exact pending marker may pass the old route-derived
capacity, cooldown, and incomplete-visit filters; every real target loss,
crowd, absence, changed route, and explicit exclusion remains authoritative.
Map every duplicate city room label and prove all current locations lie
outside the entire unchanged source route. The earlier exact-policy segment
must have stopped before departure after three waits, returned to healer,
and changed neither XP, loss, level, boot, nor its own source revision. It
must contain no kill, detour, or correction; its saved mobile, endpoint, and
commands must match the current source candidate exactly. Different source
revisions do not authorize a changed path.

A separate dynamic preflight retry may reopen one exact plain current-band
source hunt after its `where drunk` check at room 3001 finds the source Drunk
(mobile 3064) on Temple Square and exhausts three bounded checks. Arm it only
after ordinary current-band selection and city-detour rechecks find nothing
executable. The linked successful prior segment must retain the exact source
revision, policy, mobile, room, and route; unchanged level, boot, XP, and loss;
three route-preflight retries; no target, consider, kill, or combat evidence;
and a full-health return to healer 3054. The current checkpoint and exact
retryable route-hazard result must still match that evidence. Persist one
marker and consume it before connecting. It may reopen only that route's
cooldown for a fresh healer and room-3001 locator; every normal route, live
identity, consider, output, protection, and combat gate remains in force. Any
new hazard, mismatch, interruption, or failed attempt closes it permanently
for that level/boot. It does not clear other cooldowns or route exclusions.
If the target is past the three-kill fresh-search cap, the ordinary productive
repeat selector must independently admit that exact policy using all ranked
candidates and the normalized XP ledger. The route marker itself is never
productivity evidence; record `repeat_after_kill_cap` when this gate passes.
The general dynamic-hazard reset guard yields only while this exact marker is
pending and still matches the selected candidate and saved result.
Repair one legacy closed marker only when it lacks that field, records the
exact offline source/current-band gate closure, remains unattempted, and still
matches the same run, route, boot, level, and source revision. Consume that
repair on re-arming; never reopen a marker after dispatch or another failure.

Persist `campaign_field_city_clear_route_revalidation` separately, preserve the
old closure ledger, and consume it before dispatch. One marker per level/boot
is the limit. When the exact old segment is beyond the eight-row tail and
256-row metadata window, `get_indexed_campaign_phase_segment_id` may obtain
one ID from `idx_campaign_segments_campaign_phase`, then hydrate only that
segment. Missing indexes or invalid rows fail closed; never expand checkpoint
history or create an index in the observation reader. This index was prepared
once for the active historical database on October 7.

At restart, promote the consumed marker only from a linked successful segment
with the exact source mobile's positive objective kill, positive net XP, no
loss, unchanged level/boot/source, a complete run-linked unblocked route, and
safe healer return. Save the verified run/segment IDs and gain as `succeeded`.
Ordinary selection may then use that exact route with fresh checks, while the
historical blocked-policy ledger remains intact. A new live city block closes
it again. Absence, failure, interrupted return, changed route, or mere safe
execution does not promote it and cannot reopen a combat loss. Runs 16440 and
16442 verified successive useful Ki-Rin kills after this route correction;
new negative/legacy-index cases are saved but unrun until the next daily window.

Because the detour replaces route commands before the area boundary, shift any
later live-maze start and resume indexes by the exact command-count difference.
The live maze must begin at its registered entry room; stale source-path indexes
must never be applied to the longer detour.
After that correction, one prior same-boot result may be revalidated only when
it records the exact pre-combat "live maze navigation reached unregistered
room" failure, the room is on the current source route before its registered
maze entry, and the recorded maze destination matches the source route. Require
no target or consider observation, kill, XP change, crowd, or cooldown. Persist
the exact policy marker and consume it before dispatch; a second failure stays
closed. This repairs route evidence only and does not relax any live gate.
A recent level-8 Circus attempt found the Drunk at Lusty Ogres
Tavern, Main Street, and the Mage's Guild entrance, then returned safely
without engaging a target. The exact mapped bypass is admitted only when the
fresh route-level locator is clear of its rooms; that check does not depend on
an earlier healer-side flag. Existing XP, health, movement, and route gates
remain authoritative. The detour reached an actual target in run 15457; the
subsequent fight lost XP, so route execution is proved, not improved throughput
or HERO progression.

Field-city obstruction checks must use only the rooms traversed by the selected
route, not a fixed list of nearby rooms. The Mud School path from healer room
3054 goes through Temple room 3001 and then north; it does not cross Temple
Square room 3005, so a drunk there must not block that route. Routes that do
cross room 3005 still require the registered live `where drunk` check.
The source-bounded city-transit shortcut does not replace this preflight for
field XP routes; check the selected route from the healer and again at recall
before crossing any reported room. DD4's Drunk greet program attacks visible
entrants regardless of alignment, so a revealed good alignment is not a bypass;
only a fresh, practiced invisibility affect can suppress that greet trigger.

An automatic world-time probe must not preempt progression once the checkpoint
already has an authoritative reboot identity and a same-boot source policy
result. In that state, the next invocation must rotate to another executable
current-band route or report the actual protection/output/route blocker. The
periodic maintenance probe is available only from a blocked healer checkpoint
after its six-hour marker interval, or when an explicit reset-wait/shared-boot
revalidation requires it. It remains maintenance-only and cannot clear a
same-boot hunt result.

This is not a blanket reboot requirement for XP. DD4 assigns a mobile's fuzzy
level when the area data loads, so a same-reboot live below-band observation
keeps that exact reset policy closed. A separate reset room for the same mobile
may load a different level, but it must pass its own fresh live `where` and
`consider` before combat. A later reboot matters only when all remaining
source-ranked targets are closed by their exact-reset evidence or by an
exhausted protection reserve; otherwise the selector continues with any
independent current-band route immediately.

A source-ranked hunt that returns a loss-free absence is not a consumed retry.
A positive cooldown is only a short scheduling pause to avoid issuing the same
locator command immediately; it is not reboot-scoped and never makes a viable
target wait for a reset. Once the scheduler reaches a later bounded visit, it
may re-locate the same target under fresh source, route, identity, consider,
health, crowd, and loss checks. Route, crowd, combat-loss, and other terminal
failures remain separate safety evidence and cannot be reopened by this absence
rule; a fresh source-audited repair is required for those cases.

One reset-aware revalidation may reopen an exact source-ranked policy after a
pre-target runtime-boundary timeout. If that policy has already reached the
ordinary three-kill cap this reboot, require its latest eligible kill from the
same policy and reboot to have earned meaningful XP. This only admits the
bounded route check: current-band, source, movement, hazard, live identity,
`where`, consider, protection, and combat gates remain in force.

When a source-ranked route-program preflight finds its registered hazard in a
specific live room, the next same-boot selection may arm one narrow detour if
the room label maps to exactly one source room in the route origin's area and
the alternate path stays within the existing detour bound. The route still
runs its normal `where` preflight and all identity, crowd, consider, movement,
and combat gates. An off-route wandering result is evidence only and does not
block travel; an absent endpoint earns no XP but does not create a reboot-wide
pause. Ambiguous labels, missing paths, or a second changed hazard remain
closed.

When no high-confidence fresh route remains, a source-safe current-band target
with a material useful-XP fuzz probability may outrank capacity research. The
ordinary below-band floor still applies, and research or resource probes never
count as progression XP.

An exact same-level, same-reboot protection marker with no sanctuary reserve
and no executable independent current-band route is also a reset boundary. A
runner invoked with explicit reset retries returns `ready` with
`awaiting_area_reset` and opens no gameplay segment; the outer runner waits
once for the configured interval, then opens the maintenance world-time probe
only if no independent executable current-band route remains. Any such route
still takes priority and earns XP immediately. A capped invocation remains
`blocked`. This preserves the protection requirement and prevents repeated
invocations from becoming a terminal liveness failure or silently buying
flight against a higher-priority funding objective.

Once a world-time probe has observed `time` and is back in healer room 3054,
save and quit take precedence over optional health, mana, hunger, or movement
recovery. The starter may clear only a stale local combat flag when the live
room is authoritative, safe, no-mob, and not in combat; actual combat or
unknown room occupancy remains a hard stop. An explicit city-route observation
still runs before logout. This prevents a completed maintenance probe from
reopening the generic sleep/stand loop at the runtime boundary.

Before declaring the frontier unavailable, a living character already at the
safe healer with food must complete the normal bounded recovery if health,
movement, or mana is below the campaign readiness threshold. Re-select the
source frontier after waking. Low movement by itself is not a reason to spend
the one-shot reboot probe or wait for a reset.

When source ranking finds no executable target, persist
`campaign_source_ranked_frontier_diagnosis` in the checkpoint. This is an
offline explanation only: it records the reboot, level, candidate counts,
current-band and autonomous-safe counts, sanctuary requirements, and exact
same-boot below-band exclusions. It also reports
`psionic_protection_gated_count` and the matching candidates separately, so a
level-14-or-higher `spec_cast_psionicist` is visibly closed for its
energy-drain/disintegrate exposure unless a fresh protection receipt exists.
Each matching candidate now records `protection_effects`, so level-40-plus
entries explicitly show the disintegrate exposure rather than hiding it inside
a generic special-mobile rejection.
Inspect it with `show-campaign` or the
campaign state report before deciding whether a reset wait or source refresh
is justified. Never use the diagnosis to bypass a sanctuary, route, identity,
or live-consider gate.

When the two bounded current-reboot sanctuary carrier attempts are exhausted,
arm `campaign_sanctuary_area_reset_recheck` only from a living, quiet healer
checkpoint. Without a current protection-loss marker, do not let this
maintenance route preempt an executable current-band hunt; arm it only after
the selector reports no safe hunt. The outer runner may wait once for the
configured area-reset interval, then clear the exhausted result and reset the
active attempt count to zero while retaining `prior_count`, `area_reset_cycle`,
and the reset boundary. Startup repair ignores pre-boundary sanctuary segments.
The marker becomes `attempted` before the fresh route opens. If the connection
never reaches the login prompt and zero game commands were issued, restore its
dispatch marker to pending and checkpoint transport unavailability. A later
explicit invocation may use that same one-shot recheck without another reset
wait; the current invocation must stop. Once any game command is issued, a
second route failure cannot reopen it during that reboot. Acquisition or a new
reboot remains the other reopening event. A source checkout refresh must
preserve spent-marker and attempt evidence: it may invalidate source-derived
route results, but must not let generic protection fallback or an automatic
capacity probe silently re-dispatch an exhausted Moria route. The autonomous
outer runner must honor this persisted boundary across process restarts; a
spent recheck is a durable blocker, not permission to start another area-reset
wait.

That sanctuary boundary must not suppress an independent progression retry.
From the same quiet healer checkpoint, one bounded area-reset wait may reopen
only an exact, same-boot, current-level `source-ranked-hunt-*` whose live result
is absent, whose remaining absence cooldown is at most two, and which is not
city-blocked or already attempted from the city. Persist the exact hunt that
justifies waiting. The ordinary reset handler then ages reboot-local absence
evidence and reruns current-level source ranking; the saved target does not
authorize a route or combat. Every selected route still needs the ordinary
identity, route, consider, output, protection, and action gates. Do not change
the spent sanctuary marker or attempt count, and do not wait again for the same
unchanged absence result.

The initial cooldown of three may enter that existing wait flow only when the
bounded eight-segment tail proves the latest exact hunt reached its registered
endpoint, found it absent, and returned safely without XP, kills, or loss,
after a recent useful kill of the same source mobile and policy. Both visits
must retain the current level, boot, and source revision; the plain, unarmed
candidate must not require sanctuary. A source/route change, loss, missing
endpoint sighting, city block, or intervening failed visit rejects this first
wait. Save the exact policy in `awaiting_independent_absence_reset`; the normal
completed-wait handler ages the cooldown, and the supervisor's finite budget
remains authoritative. This changes wait admission only, not target permission,
sanctuary markers, or combat-loss closures. New cases await the next daily
test window.

An automatic source-capacity entitlement does not reopen general sanctuary
recovery after its retry is terminal. One exception is the exact Moria
capacity probe: a fresh, unconsumed automatic-reset entitlement may admit the
source-audited mobile **4055**, object **4050** route even when the general
sanctuary retry is exhausted. The selector must still prove the two-room,
one-entry-per-room source capacity and all required-loot route gates. Consume
that entitlement at persisted segment start; it grants no ordinary XP hunt or
general protection fallback, and a live absence closes it for this boot.
Without an unconsumed reset entitlement, the terminal sanctuary boundary
remains closed. Run 16444's extra failed attempt remains recorded and is not
replayed.

Flight funding must not strand a healthy, fed character after its safe carrier,
one ground probe, bounded current-band XP rotation, alternate funding targets,
and available bank loan are exhausted. From a fully recovered healer
checkpoint, the campaign may then re-run normal selection without the funding
override and take an executable registered policy for the current level.
Preserve the funding marker; this handoff grants no combat permission and does
not bypass the selected policy's route, identity, consider, output, or health
gates. Do not wait for a reboot solely because flight remains unfunded.
If no registered alternative is executable either, the existing
`quest-frontier-request` is available only when a source-derived QP shortfall
blocks the next level, with fresh observed quest state and nonnegative fame.
Campaign markers remain audit history only; they do not cap requests by level
or reboot. An active quest or positive live `nextquest` closes this handoff;
once the timer reaches zero, another request is eligible under the ordinary
fame, healer, and preparation checks. This does not authorize the randomly
assigned target.

An observed positive quest cooldown never pauses current-level XP. With no
active quest, let the source-ranked candidate selector check the current band;
choose a connected cooldown wait only when a positive QP shortfall blocks the
next level. Keep
active quest steps and every ordinary route, identity, consider, output, health,
and combat gate unchanged. A cooldown wait is only the bounded fallback when no
other current-band route is executable. If an earlier wait made no counter
progress and left an unavailable cooldown checkpoint, rerun the source-ranked
selector rather than repeating that wait. Active quests and an expired timer
remain ineligible for this fallback.

For the required next-level QP gate only, preserve the connected healer wait
when exactly one live cooldown minute remains and the normal fed, recovered,
safe-healer, fame, and no-stall checks allow it. Let that bounded wait request
the quest when DD4 clears the timer before opening another hunt. This narrow
priority does not apply to optional frontier requests or reopen a stalled wait.

For noncombat Circus quest objects, `quest_access.py` audits the existing
admission purchase as a prerequisite instead of treating the locked Big Top
as unreachable. Require the exact ticket object 4400, shopkeeper mobile 4400
and its independent room-4402 reset stock, and the locked south door from
4415 to 4416. The approach and continuation must pass source hazard checks,
stay within forty commands, and use no other key. The first stop buys and
requires `a ticket`; the second unlocks, opens, and follows the checked route
to the exact quest object. A different ticket does not suppress the purchase.
Changed source identities, unsafe paths, unaffordable/failed purchases, and
missing admission stop the attempt normally. Keys are not assumed to survive
logout. Kill quests retain their independent combat admission.

Flight-shopping transit can use the existing source-bounded greeter assessment
with fresh departure readiness. Permit only one isolated, exact source-VNUM
interruption in the registered city route, with source-level/HP limits, a 70%
character-health floor, nutrition, and a 60-second deadline. Normal segment
cleanup still takes precedence. Persist `campaign_city_shop_transit` outcomes,
not a resumable combat timer. A failed transit denies the same-level/reboot
allowance; missing reboot evidence cannot reopen it. Bind a short run's missing
stamp to the campaign's known reboot when merging fresh evidence. Do not erase
field losses, reopen real purchase failures, add loans, or count these weak
defensive kills as objective XP.

The bounded city-transit allowance does not reopen routine loot sales during
an active shop-route cooldown. Defer those until productive work ages the
cooldown. Only an explicit food, flight, or lockpick funding shortfall may
force liquidation through the audited transit allowance; count only observed
sale proceeds.
Do not start a proactive field fight or familiar attack while still inside this
city corridor. Only a cityguard that attacks first may enter the exact live
source-VNUM combat check above; resume ordinary hunting after leaving the route.

If the Magic Shop purchase policy reaches the healer while `fly` or
`levitation` is still active, the worker must sleep until the existing affect
expires because DD4's spell handlers do not refresh an active flight effect.
DD4 decrements positive affects every 30-second `PULSE_TICK`; the campaign
therefore caps this maintenance worker from the observed duration plus a
fixed shop/cleanup allowance. A short expiry wait may checkpoint and resume,
but it may not consume a replacement potion or spend a full stale segment.

Use exact source keywords and connection-local target IDs. Mobile, object,
room, and object-set VNUM namespaces are distinct. Never restore pending
commands, companion ownership, or timing rights from saved checkpoints.
When several source prototypes share one visible target name, an exact command
keyword may resolve the expected prototype only when it appears on that source
prototype and on no other prototype reachable in the exact room. A shared
generic keyword remains source-ambiguous; refresh persisted candidate keywords
from the current source catalog before constructing a live route.
Every route containing a registered GREET or other source program must complete
its exact `where` preflight and adjacent-room scans, even while the character is
invisible. Leave if the named attacker is found on the planned route; invisibility
does not waive detection, scripts, or unknown hazards. Fresh invisibility is
limited to separately audited ordinary aggression with no relevant programs.
Record locator results separately from the room where the command was issued,
and never treat a skipped scan or old visibility note as completed preflight.

Revision 243 grants one revalidation only for the exact current-level/reboot
sanctuary failure produced by the obsolete visible-GREET check. Archive that
result under `campaign_sanctuary_visibility_revalidation`, consume the marker
before opening the sanctuary segment, and close it as succeeded or failed from
the fresh result. Do not remove the prior XP loss, protection requirement, or
attempt count. Absence, route failure, interruption, or death does not authorize
another attempt.

Revision 246 grants one further revalidation only when revision 243 positively
located the carrier and a fresh, completed route `where` preflight found no
planned-route hazard. Old invisibility notes alone do not qualify. Consume the
marker before connection and preserve every earlier failure. A practiced,
source-authorized invisibility route may request two sanctuary potions only when
two reachable carrier resets prove that capacity. During this recovery errand,
do not consume either potion; require two positive pickups, two successful pouch
stows, and the ordinary healer return before recording two verified reserves.

Revision 245 grants one revalidation only for revision 244's exact live shape:
the carrier was positively located, one empty relocation was attempted, no
object or objective kill was recorded, and the character returned safely with
no new loss. Persist `campaign_sanctuary_locator_label_revalidation` and consume
it before connection. `where` display labels require distinct bounded coverage;
an empty relocation path cannot revisit the current room. A pending field
`look` completes only on an actual room listing, not a prompt or status message.
Retry silence once after five seconds, then return safely. Acquisition or failure
closes the marker and never authorizes another retry.

Revision 273 repairs a markerless persistence edge for the second sanctuary
reserve. It may reopen only the exact same-boot, same-level failed handoff
whose source carrier and reachable object reset are already evidenced. Preserve
the nested failed result, loss and attempt ledgers, and protection marker; the
corrected errand requests two total pouch reserves, consumes neither, and
closes after the healer return. This narrow repair does not generalize to
below-band XP hunting.

Persist sanctuary use across the whole segment for XP-loss reconstruction while
resetting the combat latch between stops so a later fight may use its own
reserve. An unprotected first loss may receive one protected retry. A loss from
a segment that spent sanctuary is already the protected attempt and must not
authorize another potion-backed retry. For source-ranked caster combat, replace
the generic `kill` opener only with the exact source-planned direct spell after
class registration, positive observed proficiency, availability, exact target,
and a post-cast 15% mana reserve all pass. Track and acknowledge that opening
cast through the normal combat command window; otherwise retain `kill`.

During the same bounded encounter, a caster may rotate to the next practiced,
source-registered damage spell after two weak attempts if the measured target
damage is below 25% of the live target HP. Each rotation resets only the finite
damage probe, is limited to the remaining known spell list, and preserves the
existing target identity, resource, incoming-damage, and withdrawal gates. A
rotation is combat adaptation, not new source admission or proof of a kill.

For an exact sanctuary-backed, passive, unarmed HP-fuzz target, a three-sample
high-health probe that is within 10% of its required damage fraction may receive
one additional two-update window. The measured exchange must remain favourable,
the target must match the exact live VNUM, and its projected finish may exceed
the audited action budget by at most one action. This is a finite observation
extension, not a retry or permission to fight an unknown special. Damage-window
withdrawals retain gross damage, regeneration, net damage, incoming damage,
target VNUM, and room as loss evidence for later output or gear decisions.

A displaced sentinel beside the planned reset endpoint may be identified from
one fresh complete room listing only when its full source description is
globally unique, its single reset has capacity one, and source plus live exits
agree on the adjacent same-area ground route. Reject random, no-mob, locked,
wall, aggressive, or scripted cases. This is explicitly source-description
inference, not a GMCP VNUM observation. Bind the exact instance to room, stop,
level, reboot, and a 30-second lifetime; discard on movement or disconnect.
Require ordinary consider, crowd, companion, resources, and combat admission.
Persist `campaign_fastwalk_displaced_target_outcomes` for audit only, never
restore identity or reopen source-route/loss exclusions from that record.
Ordinary hunts and funding trips share the early same-area locator planner.
Reset-only required-loot hunts may reuse the same locator controller with
source-bounded carrier paths. Require a known same-area, nonconfused wanderer,
the unchanged admitted carrier/loot contract, and a verified original approach.
Query before the final approach, map exact source short names, and retain
excluded labels as sightings with no executable route, not area absence.
Search at most eight source-reachable rooms within a 24-move fallback sweep;
allow at most one existing locator refresh with a separately bounded 24-move
relocation. A carrier route that requires source-authorized practiced
invisibility may inspect at most 12 rooms under the same 24-move cap. Admit an
ordinary aggressive transit mobile only when DD4 `can_see` proves it lacks
detect-invisibility, all source programs are absent, no reset equipment can
alter detection, and every special is noncombat or combat-only. The runtime
must require and maintain the live invisibility effect. Detecting, scripted,
unknown, pre-combat, and endpoint-combat hazards remain blocked. For a
source-ranked hunt that has already passed selection, a plain endpoint
``ACT_AGGRESSIVE`` target may be included in the same route invisibility
identity when the source proves it cannot detect invisibility and has no
special or program. This only prevents an entry auto-attack; capacity,
consider, HP/output, combat, and return gates remain authoritative. Both modes
share the original runtime and command limits. Paths must be
open, known, same-area ground routes without random, private, solitary, no-recall,
wall, flight, or unresolved source transit hazards. Ambiguous room names authorize
only the mapped accessible subset, never every room with that name. Preserve
pre-entry scans, exact consideration, crowd/loot checks, and all loss/retry gates.
Retain required familiar staging on the outbound prefix, the original city
preflight, exact target/consider/crowd checks, and the normal reset fallback.
For provision-funding, the same visibility contract may admit one exact
unarmed carrier of a dynamic saleable drop, including a source-safe noncombat
special such as `spec_fido`, only after the source current-band, movement,
HP/protection, saleability, and live-identity gates pass. Carry every audited
transit mobile VNUM into the `Fastwalk`, mark the segment `funding_only`, and
exclude its XP from progression. Armed ambush endpoints, rejected targets,
scripted or unknown transit hazards, and same-boot repeats remain closed.
When a live Magic Shop see-invisible quote is unaffordable, preserve that
same-reboot price and create a bounded funding handoff. Reuse the audited coin
stash/carrier selector until the quote is affordable, then allow the one-shot
shop retry; never retry the purchase blindly or enter a detect-invisibility
target without the required live affect. This handoff does not weaken the
separate `spec_cast_psionicist` disintegrate-protection gate.
After that ordinary funding selector is exhausted, one bank trip may cover a
source-ranked hunt's combined flight and see-invisible costs only when both
shop quotes are from the current boot, the visibility potion has live stock,
and the selected route actually requires both preparations. Borrow only the
exact carried-coin shortfall, bounded to 100-400 copper; if the teller directs
withdrawal instead, request that same amount. A stale or missing visibility
quote cannot authorize borrowing for an invisible target. The standalone
flight-only loan remains available under its existing current-quote contract.
Do not shorten specialised transit-recovery plans a second time. An early
locator changes travel order, not candidate eligibility, movement admission,
search limits, retries, or loss history.
An early field interception must retain its connection-local route position.
After a below-band rejection, only a matching observed waypoint on an unfinished
destination-guided leg may resume that leg. Keep the rejected sighting and
require fresh consideration at later rooms. Do not mark an unvisited endpoint
consumed or start the next leg from a fictional origin. Explicit aborts, crowd
and route hazards, changed rooms, and ambiguous command-only routes do not
receive this continuation. No new candidate, search, or retry is authorized.
An intercepted evaluation owns ordinary outbound travel until resolved. A
completed bystander audit clears primary consider state, not that ownership;
resume the shared target evaluator and require the remaining exact instance's
own result. Pending checks retain their existing deadlines and attempt limits.
Never turn a no-command evaluation into movement. Combat, emergency return,
and the segment cleanup boundary retain precedence.
Register and test skills before dispatch; positive practice, equipment,
resources, target state, and safety gates remain mandatory. Honor existing
gear-mode, provision, corpse, trainer, and prerequisite contracts in the archive.

Campaign policy revision **334** enables the cleric protection chain after its
existing damage and healing priorities: protective magiks 45%, protection 40%,
then sanctuary 40%, each only when a fresh live teacher listing offers it.
Protection reduces damage only against sufficiently opposed alignments;
sanctuary halves damage while active but costs 75 mana. Existing buff upkeep,
proficiency, and mana-reserve checks remain authoritative. The revision makes
older trainer audits stale so the next eligible segment can inspect the teacher
again; it does not grant practice or spell-use permission by itself.

DD4 source revision **7953a00** adds Knight access to `protection vs evil` and
`protection vs undead`. The prerequisite identifiers are `protect vs evil` and
`protect vs undead`; keep those distinct from the castable skill names in
training data. Maintain either ward only when the current live skill listing
proves it is known and the ordinary mana reserve passes. The undead ward can
deter fresh uncommanded undead attacks or joins, but cannot end an existing
fight. `turn undead` remains analysis-only until the controller can verify all
eligible room targets, crowd risk, damage credit, and safe withdrawal. These
new source capabilities are not live proof while the server revision and
teacher listing remain unverified.

Training-audit freshness is tracked by a fingerprint of executable base-class
and subclass priorities, separately from the campaign code revision. A changed
training graph reopens at most one same-level, same-boot trainer repair; that
visit clears old practice deferrals and records the fingerprint only after a
live practice listing is observed.

A familiar may kill during the synchronous opening order, before a player
attack or enemy snapshot exists. Adopt that completed encounter only from a
pending order in the same room, exact unique source target/selector, positive
unique companion ownership/presence, and the named damage/death pair. Cancel
the player opener, retain zero XP with `objective_eligible=False`, and preserve
normal corpse looting. Never restore this pending order across connections.
Familiar damage plus another target's death in one packet is not familiar
death. A positive familiar-loss line cancels its opening without declaring the
player's still-active opponent dead. Keep these outcome repairs separate from
proof that the player can secure the next finishing blow.

World ticks and unsolicited prompts do not acknowledge summon, look, or group.
Retain one 30-second deadline across familiar preparation; silence neither
retries nor immediately fails it. Require the fresh complete room listing after
look and exact positive summon/group replies. Explicit source refusals stop
preparation. Late replies cannot restore expired ownership. Hold ordinary
travel and attack during preparation, never emergency recovery or runtime caps.
Temporary confirmation, recitation-exhaustion, and observed-mana failures use
the existing bounded route retry, not a permanent reboot-wide exclusion.
Preserve the failed record and countdown; identity/refusal, fatal, negative
consider, and loss evidence are not cleared by this classification.

A reassembled exact-target easy-kill response must reach both the solo budget
and the ordinary consider handler. Retain the request's room, target selector,
source mobile, stop, level, reboot and freshness scope. Explicit stop rejections
still take precedence. Do not assume fixtures with a pre-existing positive
consider prove that a fresh fragmented reply completes the real decision.

A fresh exact-instance easy-kill consider can narrow an ordinary source load
to character levels -4 through -2. A solo substitution requires the current
room/stop/level/reboot binding, unique target and owned companion, audited
spell capability and positive practice, full source HP/weapon/rank/special
checks, and actual proficiency-adjusted mana costs. Use the existing encounter
controller with one target; never grant companion damage credit. Confirm the
owned companion sleeps before the player attacks, and wakes before ordinary
onward travel. Each exchange permits one exact-instance order and five seconds
for a positive outcome; `Ok.` alone and late acknowledgements do not suffice.
Emergency recovery and runtime caps remain prior authorities. Persist only
`considered-solo` budget/outcome audit records, never pending orders, timers,
ownership or consider permission across connections. This does not eliminate
outdoor preparation or its mana cost, and adds no route retries or loss reset.

When the audited player output alone covers a source-ranked target's HP
ceiling, use the bounded familiar opening handoff: issue one exact familiar
attack, require its positive acknowledgement, then issue and confirm its
withdrawal before the player's opener. This is a timing guard against the
familiar taking the next automatic round, not extra combat authority. Keep
the normal familiar requirement for stronger or underfunded targets, and
retain exact ownership, selector, room, source, and live outcome checks.
Before issuing the familiar's attack, audit every open exit it could randomly
choose when fleeing. Each destination must admit NPCs and have no source-known
aggressor, combat program, unsafe special, or mobile that can join the fight;
one safe exit does not make the others safe. DD4 rejects no-mob destinations
before stopping the familiar's fight. If the handoff is optional, proceed solo
only under the registered player-output proof; otherwise reject the stop before
the attack.
Run 13053 is live evidence for the handoff and +168 player XP on Granny
Jenkins; it does not establish sustained progression or HERO proof.
Although `mounts.are` sets the pony prototype's `AFF_CHARM` bit, `db.c` removes
that bit while loading every mobile prototype. `spell_summon_familiar` only
adds the created mount as a follower, so the live pony can leave its master.
Use `order <exact selector> flee Fear` to bypass the NPC random no-op, and
require the exact `The pony has fled!` departure before the player's opener.
`Ok.` alone is only order acceptance; do not issue a sleep order after the
pony has left. Allow five seconds for confirmation. If withdrawal is
unconfirmed, abort the stop and make one direct recall attempt when legal. If
flee is unavoidable, issue it once; after it succeeds, continue the bounded
return instead of fleeing again because a snapshot or pursuer remains. A
no-command result from the retry helper is still a failure boundary; it must
not fall through to the player's damage selector or resume automatic combat
actions. In-place sleep is valid only for a separately verified charmed
companion that remains in the room.

DD4's `fight.c` awards a familiar's finishing blow to its owner only for the
witch, infernalist, necromancer, knight, and werewolf subclasses, or an
unsubclassed shifter. For other class/subclass combinations, start the ordinary
familiar withdrawal at 65% target HP instead of 45%, giving the player more
room to secure the XP. This changes only the handoff timing; target admission,
combat budgets, and emergency recovery remain unchanged.

Treat source aggression text such as `grunts as he takes a swing at you`,
`grunts and swings at you`, and `takes a swing at you as you enter` as
immediate `combat_started` evidence, even when `Char.Enemies` has not arrived.
This closes the pre-combat familiar and route-preparation workflow on the same
read; it does not grant combat permission or replace the authoritative GMCP
identity and damage gates.

For an admitted solo encounter, reprice continuation from remaining enemy HP,
current mana, observed outgoing/incoming damage, and the original command/time
budget. Do not apply the generic opening-damage fraction as an additional solo
veto. Retain source identity, companion standby, health reserves, no-progress
deadline, spell acknowledgements, and emergency withdrawal. An offline repair
does not clear the failed route's actual loss history.

Record raw input beside derived observations, reject malformed enemy snapshots
without erasing combat, and retain real loss/death history. Flush SQLite event
batches before asynchronous waits. Use indexed, bounded read-only queries for
inspection; do not scan entire transcripts or giant checkpoint histories.
Normalize CR-LF and LF-CR pairs once, including pairs split across packets,
without removing real blank lines. Reconcile each flee penalty and partial-XP
refund with its authoritative GMCP change; a prior loss in the same connection
must not disable deduplication. Compare raw progress with derived checkpoints
when totals disagree. Record corrections explicitly, preserve historical raw
events and real losses, and do not report an accounting correction as earned XP.

Separate gross shop prices, carried currency, and bank debt when reporting
funding. Current sale/proceeds records store gross values. A loan notice means
source `do_sell` credits integer half the price to carried money and half to
debt; odd-price rounding can lose a coin. Reconcile against fresh currency
snapshots and distinguish sacrifices, loot, purchases, and sales. Do not infer
spendable income or a sustainable money loop from a sale acknowledgement alone.

Reconstruct source circuits by observed stop identity, not only segment phase.
Use the authoritative run kill ledger, including explicit empty results. A
secondary kill must not promote the headline or inherit another stop's crowd.
Preserve newer negative results, whole-run death/failure, and actual segment
reboot scope. Do not let inherited result metadata override that scope.
Revision-242-and-newer terminal records already contain per-stop results; the
legacy consider migration must not rebuild them and resurrect old failures.

Funding remains objective-bearing when its authoritative ledger contains
positive, eligible XP tagged with the exact source policy and carrier VNUM.
Project only that carrier onto hunting research, retaining the funding phase,
raw ledger, and existing kill counts. Failed, fatal, XP-losing, unknown-XP,
wrong-identity, superseded, or other-reboot runs cannot promote route proof.
An explicit reset clear is superseded only by a successful attempt whose
timezone-aware start is demonstrably later than the latest matching reset
checkpoint. Unknown ordering keeps the clear. Do not resurrect older proof.
Compare an exact same-reboot latest gross sale with a known current flight
shortfall only as an income upper bound. A low-yield funding preference may
yield to an already executable ground hunt, never skip food or protection,
add a loan, or manufacture another reset allowance.
When a live funding candidate has no audited coin balance or measured
same-reboot proceeds covering the shortfall, a failed funding route, including a
completed kill whose liquidation produces no sale proceeds, may hand back to an
executable source-ranked current-band ground hunt without flight for at most
three attempts at that level and reboot. Persist its policy identity before
dispatch, then return to the funding handoff; do not turn the exception into a
ground-hunt loop or wait for reboot while safe current-band XP remains
available.
There is one more exact funding route for the current flight shortfall: the
Gnome treasury in room 1570 contains source money objects 1516 and 1517 worth
1,240 coins nominally. `db.c` independently fuzzes each denomination above ten
by ten percent in either direction unless `ITEM_DONOT_RANDOMISE` is set, so the
guaranteed total for these objects is 1,175 copper-equivalent. Compare the
current shortfall against that minimum, not the nominal total. The route crosses
eight reset entries for level-3 hobgoblin guards, but DD4's `update.c` skips
aggression when the player is more than ten levels above the mobile. Admit this
stash only when the source rooms, object VNUMs, crowd limits, route-program
audit, movement budget, and minimum payout all match. Record it as
`funding_only`; it is never ordinary XP permission, and a changed crowd or
source identity closes it.

Funding completion and objective eligibility are separate ledgers. A source-
identified below-band kill may complete an explicitly selected provision-funding
action and age its retry cooldown, while its XP remains excluded from objective
progression. Prefer the funding segment's durable `completed_kills` event over
an empty `objective_kills` list, and repair its completion marker on resume from
that exact run only. A completed funding action advances cooldown even when its
XP delta is zero. An observed below-quote balance remains actionable despite a
retry cooldown; negative fame must not override that safe funding path. None of
these repairs authorize another target or promote low-value XP.

Treat source objects flagged `ITEM_POISONED`, `ITEM_CURSED`, `ITEM_NODROP`, or
`ITEM_NOREMOVE` as non-tradeable until live shop evidence proves otherwise.
Their area-file value is not funding evidence. If a compatible shop returns
zero, retain the refusal and use the bounded donation/sacrifice cleanup path;
do not repeat the same shop route as a money loop. Likewise, an equipment
object with a known negative stat modifier, especially a ring with `-2 str`,
must not be retained solely to fill an empty wear slot. A quarantined
`bank-excess-coins` handoff may fall back to liquidation when saleable surplus
is present, but the resulting proceeds must still be observed before flight or
food service is retried.

Crowd assessment shares the existing three-probe, five-second-response budget
across single and repeated mobile identities. Require complete, unique live
selectors and source-identified ordinary mobiles. Only an exact source consider
response at or below the -5 band discounts that instance; unknown, refused,
expired or changed instances remain material. Another target's consider is
never attack authorization. Preserve level/reboot/room scope and all combat-loss
gates. Pin an ongoing source fight to its considered instance across GMCP name
changes and room refreshes; never redirect it to a same-name replacement.
Telnet GMCP currently repeats
the primary enemy record for some other combat participants, so duplicated
records do not provide authoritative identities or levels for those attackers.

An ordinary unarmed pair may use the source-estimated encounter envelope only
after two exact, fresh easy-kill considers and the normal route/target gates.
Require near-full health, source HP/peak bounds, executable class damage, and
mana priced by observed practice, not the spell's minimum alone. Retain the
source estimate as an estimate: compare combined incoming damage with measured
output while preserving emergency, unknown-attacker, and runtime exits. Both
kills share one 45-second/action budget and the original exact selectors.
If the second target has not joined, refresh and consider it normally. Movement,
disconnect, level/reboot change, or expiry discards the allowance. Persist only
audit outcomes under `campaign_fastwalk_encounter_budgets`, never reusable IDs
or combat permission. Do not erase crowd/loss evidence to force live admission.

An ordinary source-ranked stop may opt into one source-material bystander when
the room contains exactly one exact primary target and one distinct, uniquely
selected bystander. Require fresh easy-kill considers, source identity for both,
ordinary non-aggressive/non-scripted/non-special prototypes, no reset weapons,
known HP and damage modifiers, bounded reset population, near-full player
health, and one combined source budget that fits the six-action finishing
window, health reserve, and practiced resource cost. This path is never valid
for required loot, source coins, sanctuary or other protected probes, familiar
routes, or an ordinary unresolved route hazard. A single route-program
attacker is an exception only when the generated source audit proves the exact
program, mobile, level band, route, and bounded damage; the normal city/transit
gate and every other safety check still apply. It is enabled only by the
generated source-ranked stop flag; do not infer it from a name or from a generic
crowd count.

After the primary opener, the live GMCP enemy set may contain only the two
admitted source VNUMs, with the primary still present until it is defeated.
An extra, unknown, armed, special, scripted, malformed, out-of-band, stale, or
scope-changed enemy clears the admission and withdraws. Movement, reconnect,
level/reboot change, expiry, or a failed budget reprice also clears it. Record
admission, live budget, and cleanup outcomes under
`campaign_fastwalk_encounter_budgets`; these records are evidence, never
reusable combat permission. Current tests cover the path; no live acceptance
or progression claim follows until a fresh DD4 run completes it.

The server currently masks GMCP alignment as 50000 below level 10 and sends
the clamped -1000..1000 player value from level 10 onward. Preserve the raw
wire value, but never use the mask as real alignment. A revealed value at or
above 300 is necessary for the `spec_guard` special's own assistance path;
`violence_update` is a separate gate and suppresses a good bystander only
when both the bystander and player meet the exact 350 `IS_GOOD` threshold.
Use the player's alignment for player fights, not the NPC target's alignment.
A source-ranked target carrying exactly `spec_guard` is admitted past the
target-special gate only when the target and revealed player both meet that
350 threshold. Its source headbutt/smash/kick peak is included in the ordinary
damage budget; unknown alignment, mixed target specials, and every other target
special remain rejected. A guard elsewhere in the room has an independent
special: `spec_guard` and `spec_sahuagin_guard` examine the room occupant's
alignment below 300 while that occupant fights an NPC. For our fight, that is
the player, not the NPC target. There is no level cutoff in that path. This
corrects the earlier target-alignment interpretation after reviewing run 15984
and `special.c:spec_guard`/`spec_sahuagin_guard`. The 350 ordinary-assistance
gate and live non-hostility requirement remain separate and mandatory.
The GMCP and MSDP server paths differ; this is not evidence of corrupted
transport. Field city preflight shares the existing three 12-second healer
waits and locator parser, scoped to the actual source route plus fountain. A
completed absence or off-route observation permits normal departure; silence
does not. Keep its `campaign_field_city_preflight` audit separate from
shop-funding flags and retain ordinary combat/loss gates.
If a reported wandering-greeter location set has no safe detour, keep the
detour allowance available for a later fresh location set during those same
three waits. Apply at most one healer-side detour plus one changed-input
correction, either at the healer or at room 3001; do not extend the wait budget
or permit another correction after its fresh hazard check.

A successful field run that positively reports `stopped_before_departure`,
zero outbound movement, current level/reboot, a living noncombat healer state,
unchanged known XP and no kills is a departure deferral, not a target attempt.
Use only fresh runner evidence, never a merged old preflight marker. Checkpoint
the run and spent segment, retain prior funding and loss history, and stop the
invocation before target-outcome reconciliation or destination rotation. Failed
or interrupted runs keep normal recovery handling. Old historical outcomes
are not silently reclassified from incomplete markers.

Checkpoint cleanup is not a new maintenance observation. Pass
`fresh_observation=False` when reconciling an already-merged checkpoint; do not
assign an inherited field abort to the last funding candidate. Repair an already
replayed hazard only from the latest successful connected funding segment:
matching level/reboot/candidate, a newly completed acquisition, identical
inherited abort at start/end, no owning funding hazard in either segment state,
and a living noncombat healer return with known XP and no loss. Retain other
candidate hazards, source results, losses, and reset history. A later failed or
interrupted funding segment prevents clearance. Run this check after legacy
candidate inference so that inference cannot restore the cleared candidate.

Do not confuse declining a low-XP target with escaping an already-started fight.
An isolated, source-matched below-band endpoint attacker may reuse the existing
30-second active-encounter budget, including practiced spell costs and measured
damage checks. Require its fresh exact selector, registered endpoint, at least
70% health, nutrition, and no pending return, familiar, or runtime boundary.
Unknown, armed, scripted, special, extra, or out-of-source-band attackers retain
their rejection gates. Preserve the below-band sighting and incidental kill;
never promote it to objective XP or deliberately start another such encounter.
Discard the identity on departure/disconnect, and reject changed level/reboot,
selector, stop, or an expired timer. Checkpoint audits are not permissions.

Funding locators may run before reaching a wandering carrier's reset room.
Shorten only a fully known existing approach, retain its city/preflight origin,
and require an ordinary traversable same-area observation point. Random exits,
unresolved doors, missing source links, and hard route hazards retain the old
approach. Build source paths rooted at the actual locator origin; preserve the
reset-first fallback, exact source short-name matching, unknown/absent-location
handling, one relocation limit, and live target/consider/crowd/resource gates.
Do not change the candidate's source identity or reopen funding/loss history
merely because its observation point moved.

Required-loot endpoints may hand one exactly identified ordinary bystander
to the shared pre-combat consider/crowd evaluator only while a single carrier
is visibly identified and no combat has begun. Preserve the existing probe
and wait budgets. A fresh exact below-assistance result can discount that
instance through the existing encounter scope; it does not authorize the
carrier or survive reconnect, movement, expiry, or changed identity. Use the
registered target's exact matching rules: `orc` is not `large orc`.
Aggressive, scripted, special, ambiguous, or already-engaged cases retain
the required-loot safety path.

When the carrier is absent, do not confuse passive-room transit with combat
admission. The existing absence/search path may continue only with exact known
room instances, no aggressive mobile or program, and specials from the existing
noncombat/combat-only registry. Require the next already-planned same-carrier
endpoint, a current live exit, known open source links, and the normal locator
path restrictions; unknown, random, private, no-recall or flight-dependent paths
do not qualify. Ordinary resource and runtime returns retain priority. Preserve
the absence and existing area-presence evidence separately. Do not attack the
passive crowd, fabricate carrier presence, add a search or restore a pending move.

For a source-ranked target whose source HP range crosses the character's live
HP ceiling, pass the exact GMCP `Char.Enemies` records already validated by the
endpoint gate into the source damage-budget check. The budget is the audited
opening conservative damage plus the bounded repeat-action output; a live
maximum HP above it must stop opener and potion dispatch and close that target
for the current level/reboot scope. A plain, source-identified passive target
may instead pass exact `consider`, consume sanctuary, and open combat before
the first `Char.Enemies` HP snapshot; this is allowed only for the protected
HP-fuzz probe, with an audited exact selector, no script attacker, no special,
and no weapon. An aggressive target may already have engaged while its arrival
snapshot is processed; a resulting flee penalty is real evidence to retain,
not a reason to retry the same target. Never erase the loss ledger or
reclassify this boundary as a successful hunt.
The exact unprotected plain-target HP-fuzz exception above is narrower: after
its source lower-bound and uncertainty-gap checks, its first exact live maximum
may reach the bounded damage-window probe only when it does not exceed the
source-audited target ceiling. It is not permission to continue above the
measured output or health budget; targets outside that exact contract still
withdraw at the live ceiling check.
Before dispatch, reject an aggressive XP endpoint when its minimum
source-fuzzed level is at or below `character_level - 5`. Equality is unsafe:
the live mobile can load at that exact floor and attack before `consider`.

One separate source-ranked exception covers a plain, unarmed, unscripted
aggressive target only when its route carries the exact audited `where`
preflight and every transit aggressor is independently bounded. The runner may
consume sanctuary before the exact opener and obtain one live HP/damage-window
probe; the lower source HP bound must fit the fixed output budget, and any live
GMCP ceiling above that budget still forces withdrawal for this protected
opener. The separately admitted unprotected HP-fuzz probe follows the narrower
pre-probe handoff above and still requires its source ceiling and measured
damage window. This does not authorize special, armed, scripted, or otherwise
uncertain aggressive targets.

When sanctuary recovery is cooling, the runner may also try at most eight
distinct plain, unarmed, source-safe current-band targets without sanctuary.
For an HP range above the character ceiling, both the lower bound and the
uncertainty gap must fit the audited attack budget. The live endpoint then
checks the target's actual GMCP HP before the exchange can continue; a target
above that budget causes an immediate withdrawal and closes the fallback for
the reboot. This is a bounded attempt to keep XP moving, not permission to
repeat a losing route or ignore protection evidence.

A meaningful, same-boot productive kill for the exact source mobile and reset
may clear only the indoor familiar HP-fuzz gate for a repeat when no XP-loss
record exists. It does not clear current absence, crowd, route, consider, or
source combat-output evidence, and it does not authorize an unproven target.

For the same narrow HP-fuzz hurdle, two independent solo kills at exactly the
previous character level may support the matching plain, unarmed reset one
level later. Rebuild the receipt from the same-boot objective-eligible kill
ledger, safe completed run summaries, and bounded transcripts with observed
GMCP affects and no Sanctuary use; require the prior fights to stay above the
20% floor and current HP to be at least 95%. Match character, class/subclass,
mobile, reset room, and source policy exactly. The prior GMCP target max HP
must fit the current conservative source output budget. This is not an XP or
combat permission: the endpoint must still match the live identity and max HP,
pass `consider`, and pass the damage-window, output, and abort checks; any XP
loss closes the exception.

After that kind of productive kill, the exact route may also re-enter the
recent-kill rotation before its three-kill cap when the fresh frontier is
exhausted. This is a bounded fallback, not a repeat loop: current presence,
crowd, consider, route, health, and output gates still decide the next segment.

An audited special procedure may use the same pre-opener sanctuary handoff only
when its source stop is exact, unarmed, nonaggressive, and free of attack
programs, with a source-audited route and a fixed lower-bound output window.
Consume the verified sanctuary reserve before the opener, then require the
authoritative live HP ceiling and damage-window result; entry-attacking or
uncertain specials remain blocked.

A protected plain target may cross the ordinary source HP-fuzz level ceiling
only when its nominal source level is exactly character level plus one and the
existing level-ceiling admission, sanctuary, route, and lower-bound output
checks all pass. Carry that explicit probe flag into the stop so the endpoint
allows character level plus two, checks exact live level and HP, and consumes
no potion when the live budget fails. This is a single bounded measurement,
not permission to widen the level band generally.

DD4's `quest.c` rejects every new quest request while `pcdata->fame` is below
zero, before generating a target. Treat that refusal as durable eligibility
evidence and do not retry new requests until fame is nonnegative and freshly
observed; missing fame is also a hard block. Only a completed kill quest adds
positive fuzzy fame. Object, retrieve, and hoard completions award other
rewards but no fame. An already active quest may continue through normal
completion; the negative-fame gate applies to requesting a new quest, not to
abandoning or resolving an existing one.

For a normal fame-positive kill, DD4 requires a victim at least six levels
above the player (`victim.level - player.level > 5`). A famous or infamous
source mobile follows the separate `ACT_IS_FAMOUS` branch; never treat the
ordinary six-level rule as permission to attack that exception.

The campaign orders that recovery deliberately: first admit any reachable,
source-audited direct ground gear reset that improves the combat envelope and
does not require combat; then reconsider an eligible fame-awarding kill. A
pending flight-funding marker must not hide that no-combat upgrade pass, but it
continues to block flight-only and carrier actions until their own gates clear.

October 12 NZST run **17552** refreshed Dorrik's level-37 tree at healer room
**3054**: enhanced damage **68%**, second attack **64%**, third attack **63%**,
stun **67%**, kick **68%**, Flamestrike **48%**, and **zero** physical or
intellectual practices. The live learnable list includes rescue, conjuration
magiks, riding techniques, inner force, and swim. Source shows Warrior Inner
Force can lead to Fast Healing (**40%** group prerequisite), which improves
natural HP recovery; Bash is door-only, while Warcry adds hitroll/damroll but
requires at least **16 Intelligence** (Dorrik currently has **12**). Do not
spend or detour with an empty balance. At the next real practice gain, recheck
the current class tree and exact teacher; prioritize useful damage, attacks,
control, protection, and recovery skills by measured combat value, not by a new
learnable label alone. Run **17552** killed the warehouse overseer for **1,707
XP**, ending safely at **1,148,396 XP**, **33,954** from level 38. Run **17553**
confirmed the same target absent without a loss, but the same-level, same-boot
field-city route-attempt marker still includes this policy, so the retry selector
excludes it from the independent reset wait. Preserve that marker; do not retry
or wait on this route until its registered route-clear evidence changes. Run
**17554** returned safely to room **3054** at full health; it added no XP or
practices.

Run **17560** refreshed the level-37 skill listing: enhanced damage **68%**,
second attack **64%**, third attack **63%**, stun **67%**, kick **68%**,
Flamestrike **48%**, and healing magiks **52%**. Physical and intellectual
practice balances were both **zero**; learnable entries included conjuration
magiks, inner force, rescue, riding techniques, and swim at **0%**. No lesson
was actionable, so keep current-band XP progressing and recheck the full class
tree as soon as practices, an unlock, or level changes.

On October 12, run **17571** safely returned Dorrik to healer room **3054** and
logged out without XP change. He remains level **37**, at **1,148,426 XP** with
**33,924 XP** to level 38, **18 QP** and no next-level shortfall, and zero
physical or intellectual practices. Autonomous preflights saved checkpoints
**51616** and **51617**, both before any game connection. Keep the active skill
plan focused: disarm needs Warrior **30%**, grip **85%**, and defense group
**85%**; grip is **99%**, defense knowledge **65%**. Recheck and train the
defense prerequisite as soon as a physical practice is earned, subject to the
live listing and teacher cap.

The adjacent-level unprotected-kill evidence now accepts candidates whose
source route requires a live locator preflight; it does not waive that route
check. Offline validation found two safe level-36 Yeun Sun Ho kills (runs
**17449** and **17452**) with observed target maxima of **782** and **925 HP**,
within Dorrik's current **2,784** source-output envelope. The level-37 Yeun
policy remains explicitly city-blocked, however. The one level-37 city-clear
marker was already consumed for a different Lotus Temple mobile (**10736**),
so do not transfer or retry it; its status is still `attempted`. The Dwarven
Dancer policy retains explicit level-36 and level-37 XP-loss evidence, while
the warehouse policy has extensive same-boot kill history and a retry cooldown.
Do not clear those records or wait for a reboot. Continue source-ranked current-
band selection for another eligible policy; no live hunt has yet passed these
gates since checkpoint **51617**.

### Source-Ranked Random-Exit Relocation

When a fresh positive `where` label has no registered route from the character's
current safe room, one bounded fallback may stitch only edges already present
in that source-ranked locator's safe relocation paths. It applies only to an
exact ordinary wandering target: source-known, unarmed, unprogrammed, without
specials, and outside protected, probe, resource, or crowd exceptions. The
reported label must map to an unsearched room in the same source area and
mobile search graph. Require a current live exit for the first step, the normal
movement capability and route-hazard checks, and cap the stitched route at 24
steps or three times the locator retry limit, whichever is lower. Navigate
inside only those stitched room VNUMs using each room's current GMCP exits;
preserve registered recovery rooms as separate stops. At the destination,
normal live room identity, selector, consider, and combat gates still apply.
This repairs navigation evidence only; it never widens target or attack
permission. If any source, movement, hazard, or live-exit check fails, keep the
existing bounded return behavior.

### Moria Locator Recheck

DD4's `where` command uses normal visibility rules but returns room labels,
not VNUMs. When a source-audited wandering carrier is positively located in a
label that maps to the current source room, and a locator refresh has no
movement path left, the runner may issue one additional `look`. This is a
look-only recheck for the live timing race between locator output and room
arrival; it never selects a target by locator text alone. The ordinary exact
room listing, source identity, consider, crowd, HP, and combat gates still
authorize any attack. Unknown labels, ambiguous source routes, stale absence,
and exhausted rechecks retain the existing bounded return behavior.

The shallow Moria sanctuary carrier has one additional source-configured
endpoint re-scan when room 4064's adjacent scan sees the registered warrior
4051. The runner waits briefly, rechecks the same room, and still recalls if
the hazard remains. This is a navigation timing repair only: it never permits
fighting the warrior, does not count XP, and does not widen the Moria route.

For the deep Moria sanctuary route, the source mapping currently includes
rooms **4063**, **4066**, and **4065** for the repeated `The maze` label. The
reachable path to those rooms must not cross the source-registered poisoner or
sentinel branch (**4057**, **4058**, **4062**) or the aggressive branch at
**4067**. The locator may narrow the existing exact inspection stops to this
set, or use one bounded source relocation; it must not infer a VNUM from the
wire label, search every same-named room, or treat run **13121**'s positive
area sighting as potion-acquisition evidence. A successful live listing,
consider, required-item, and healer-return sequence remains necessary. Policy
revision **283** may reopen one exact same-boot, no-loss level-24 exhaustion
result after a source-mapped locator graph change; it preserves the old attempt
and does not authorize a second unbounded retry.
At room **4064**, a positive `The maze` result may detour to one exact safe
mapped room first, but an empty inspection must return to the still-unvisited
registered stops (including **4020**, **4152**, and the later carrier rooms).
That locator detour cannot replace or complete the rest of the route.

The source-ranked deep sanctuary recovery route is flight-required from level
19, and from level 16 for a mage. DD4 reduces ordinary non-underwater movement
cost to one third while `AFF_FLYING` is active. Select flight through the
existing bounded purchase workflow before dispatch. A missing `affects`
snapshot is unknown: request one live `affects` refresh, then return safely if
`fly` or `levitation` is still unconfirmed. Targetless transit stops do not
require the purple potion before the route reaches an exact carrier inspection;
the required-item objective applies at carrier stops and at run completion.
Offline coverage was added
2026-09-30 but not run because that day's regression batch was already used.
Dorrik's latest checkpoint has an active flight affect, but a deep Moria trip
with flight and sanctuary acquisition remain live-unproved. His original
same-boot general sanctuary recheck is spent; do not repeat its reset wait or
ordinary retry. The one distinct route-suffix correction for safe run **17547** /
segment **17037** was consumed by run **17560** / segment **17050**. The positive
maze locator reached room **4063**, found no carrier, and safely returned after
the original 4020 route (which began at 4012) could not be replayed from 4063.
No further general Moria attempt is authorized on this boot; preserve the
original evidence and spent marker. The general suffix repair now re-roots only
the first unvisited VNUM leg through a bounded source-safe bridge and fresh live
exits, then preserves later stops. It grants no reset wait or combat permission. A
separate, unconsumed automatic-reset capacity entitlement may dispatch only
the exact mobile-4055/object-4050 maintenance probe below. It does not reopen
general sanctuary recovery or authorize XP combat.

Run **18250** / segment **17684** later used the exact room-4064 entitlement and
ended safely at the healer: its sole fixed-room target was absent, with no kill,
XP change, or cumulative-loss change. Because mobile **4055** wanders through
source-mapped Moria rooms, that precise miss permits one locator-only
revalidation while boot, level, source revision, XP, and cumulative losses stay
unchanged. Consume its receipt before dispatch; require a recovered healer,
current flight reserve, the eight-relocation bound, exact source route gates
(4053/4056/4050 in rooms 4058/4057/4062), and all normal live identity, item,
consider, hazard, and return checks. A miss or abort ends Moria retries for this
boot. Run **18252** / segment **17686** consumed this exception, found no potion,
and returned safely to the healer; it recorded 80 incidental XP from one
source-authorized route-gate kill. Do not repeat it. This does not clear a combat
loss, authorize fighting a route-gate mob outside that exact route, or grant
progression-XP permission against the carrier. A source refresh cannot reset
this consumed same-boot, same-level receipt; the exact attempt history remains
closed even when its original route revision is older than the current source.

The 2026-10-09 all-area source inventory found no second executable sanctuary
reserve for Dorrik at level 30. The level-27-to-33 ettin's blood (#17029) is in
a chest behind the keyed west door at room 17220; its key (#17021) is carried
by Redbeard in room 17218, but the 99-command route crosses audited aggressive
and special hazards. The sanctuary scroll (#13345) is nested in chests in the
disconnected Catacombs, while the reachable ground pill (#20645) has minimum
load level 31 and a source hazard on its route. Checkpoint 49500 has no pending
capacity-reset entitlement, and the ordinary post-reset recheck is already
marked attempted. A later, separately recorded automatic-reset entitlement may
still authorize one exact room-4071 mobile-4055/object-4050 refill after the
prior refill was consumed. Consume that entitlement before dispatch; its
failure closes the same-boot refill and does not reopen general sanctuary
recovery.

For the exact level-20 generic protection-recovery transition, a source-backed
fallback may use up to eight bounded locator relocations after positive carrier
evidence. It admits only source mobiles **4053**, **4056**, and **4050** in
rooms **4058**, **4057**, and **4062** as below-band required-loot route gates,
with exact live identity and `consider` checks. Any gate kill is incidental and
cannot earn progression XP. This does not widen the deep route, waive special
or unknown hazards, or change the ordinary +6 fame rule; live validation waits
for the next MUD area reset or reboot.

For ordinary unarmed source-ranked targets, a same-room prototype ambiguity may
be resolved only when all reachable source prototypes have identical audited
combat, special, equipment, and reset-object profiles. TARGETMODE's exact live
instance selector is then recorded with the observed alias VNUM. Resource,
special, protected, bystander, and probe stops remain strict prototype-VNUM
matches.

### Equipment Placement Admission

Source gear reports are planning evidence, not permission to walk or fight. A
direct ground reset must carry the shared route audit used for resource stashes,
including closed doors, movement capabilities, aggressive or scripted mobiles,
special procedures, crowds, and destination hazards. `promising` and `caution`
rows still require the campaign's live identity, consider, resource, combat,
and healer-return gates. `reject` rows are blocked. `source-only` rows have no
current executable candidate and must never be dispatched as a fallback. Mob
carried/equipped placements likewise retain their complete hunt candidate
hazards; a shortest source path alone is insufficient. The executable carrier
path requires an exact source mobile, room, and object match, one source spawn
for both mobile and room, a clean bounded route, a fitting live HP budget, and
the normal movement, sanctuary, protection, provision, and funding gates. It
dispatches one bounded kill, then verifies the required object before issuing
the exact loot and equip actions. A successful offline ranking or replay does
not prove that the carrier is live or that the upgrade has been acquired. If a
direct, no-combat ground reset is available, the campaign may select it before
waiting for a sanctuary recovery route or attempting a carrier upgrade. The
sanctuary gate still applies to every placement that requires entering combat.
A ground-reset pickup must wait until the live room equals its registered reset
room. A matching name or description earlier on the route is not proof of the
source prototype: DD4 can place different same-named objects in different rooms,
and live object selectors are not prototype VNUMs.
When a Warrior or Bounty Hunter still lacks its required stun weapon after the
bounded shop-rearm attempt has been spent, a direct ground reset may supply a
source-verified blunt weapon. Keep the best primary wielded and retain the blunt
weapon in inventory for the existing pre-combat stun opener. The item must be a
registered ground reset, and the ordinary live route, exact-room, capacity,
return, and identity checks still apply; this does not admit a carrier fight or
authorize combat on the acquisition route.
If source-gear setup itself fails before a run is created, reopen that exact
object/reset once only from a persisted marker tied to the failed segment,
checkpoint, level, boot, and source revision. Require `run_id` absent, zero
commands, and unchanged character state; consume the marker before dispatch.
Any connected run, command, movement, target sighting, loss, or XP change closes
this setup-only revalidation.
A protection-recovery fallback may retain one independent, source-audited plain
target even when its fresh useful-XP probability is below the ordinary ranking
floor, but its source HP range must satisfy the same audited output-window rule
even when a passive endpoint can reveal live HP before the opener. It must also
pass the live route, movement, consider, and healer-return gates. Same-boot
below-band evidence for that exact source mobile remains a hard exclusion; the
fallback never converts a known low-XP target into progression credit.
After one source-gear placement is acquired successfully, defer further gear
research for that character level and MUD boot. This prevents successive
successful or failed upgrade trips from consuming the progression session;
reconsider the loadout after a level transition or a new boot, while each
individual placement still keeps its own exact item, route, carrying, and live
verification rules.

### Daycare Ring Recovery

The optional ring objective is source-specific: only the room-6605 old-doll
reset (mobile 6605) equips pink ice ring object 6601. Confirm the exact live
carrier selectors before one bounded attempt: both reset-load dolls must be
present, and the last exact selector identifies the ring-loaded instance. If
fewer than two selectors are present, return without a kill. Verify the ring
before loot or equip commands. A below-band consider is expected for this
required-loot task: it grants no progression XP and must not permanently close this policy.
After a miss or crowd abort, retain a three-segment cooldown across reboot,
decremented only by positive-XP, non-maintenance work at the same level.
Sanctuary,
healing, food, and flight reserve hunts are resource maintenance even when a
required carrier grants incidental XP. Exclude those executions from both
normal countdown and bounded-history reconstruction; do not let supply kills
trigger another optional ring search. Recheck live
route hazards and crowd on retry; the exception never relaxes combat, identity,
health, or healer-return gates.
If this errand was already the eligible policy before current-band fallback,
it may run once that search and the exhausted sanctuary route have no safe
option left, but only from the healer with no active quest and an observed
zero QP shortfall. It remains maintenance, not progression XP.

If a
required-loot expedition withdraws after bounded source-absence sightings, keep
that raw terminal evidence and recover it at startup; apply the registered
current-reboot cooldown before retrying the exact route. The sole revision-279
exception permits the exact Moria sanctuary carrier with global capacity two
only when source proves one reset entry in each of its two audited rooms; it
authorizes one bounded maintenance attempt, never ordinary XP hunting. A fresh
generic capacity entitlement armed by a completed automatic area-reset wait
may reopen that same audited carrier once, even if the general sanctuary
attempt counter is exhausted; it never resets that counter or reopens the
ordinary sanctuary route. The entitlement is source-narrowed to mobile
**4055**, object **4050**, rooms **4064** or **4071**, global capacity two, and
one room entry; it is consumed in the persisted segment start before
connecting. A live absence closes the probe without XP credit and cannot be
replayed in the same boot. The
level-11 Mage frontier then has one distinct continuation: after a zero-XP
Moria result, try the existing one-kill Fleshmonger guard policy once. It
still requires fresh live target identity, consider, route, output, and health
checks; a zero-XP result closes that policy and returns selection to the
source-ranked frontier.
explicit `--retry-stalled` path has a separate, equally narrow Forest
bear-claw exception for a level-10-through-29 thief who still needs the
source-validated piercing upgrade. It can open only from the healer after the
current-band output-fitting frontier is empty, food and water are present, and
the normal route, movement, weight, protection, and live combat gates pass.
Record the boot, level, source revision, and policy before connecting; close
the marker after that one attempt, whether the claws are acquired or not. This
is gear maintenance evidence, not permission to repeat a failed route, ignore
a below-band target, or claim progression XP.

The source-verified Shadow Keep fine-dagger plan is a separate multi-step
Thief route. It is selectable at level 24 or above when the character
needs a strictly better piercing weapon, has the observed currency ledger and
capacity for the source lockpick plus dagger, and has a sanctuary reserve. The
plan buys lockpick object 38 from shopkeeper mobile 3050 in room 3120, trains
the source prerequisite `thief base` to 30% before `pick lock` to 60%, returns
to healer room 3054, and follows the source-replayed route to room 16619. It
uses `pick west`, `open west`, and the exact endpoint chain to room 16635,
where smuggler mobile 16609 is source-reset with equipped dagger object 16614.
The smuggler's `spec_thief` procedure is economic rather than combat-damaging,
but the plan still caps 20%-of-carried-coin exposure at 250 copper and retains
but the plan still uses an explicit level-plus-two ceiling, caps 20%-of-carried-
coin exposure at 250 copper, and retains the sanctuary-backed live HP and
damage-window probe. This +2 allowance is limited to this source-identified
economic-special gear plan; it does not change the ordinary +6 fame rule.
Source cost is a funding
floor, not a promise that a reboot's live shop price is identical; an actual
purchase failure must checkpoint as evidence. Source replay and offline
selection do not prove live purchase, door entry, combat, or loot acquisition.

`show-resource-sources` exposes protection and energy-containment resources and may also expose a
`source_analysis_route` for a source-only placement that is hidden behind a
locked door. Its
`route_key_objects` and `route_key_sources` columns identify the source key
and mobile resets that could satisfy the paper route. This is provenance for
future research only: the route is not executable, and the campaign must not
infer a safe key-acquisition expedition from it. The source mirror preserves
the raw `M`/`G` reset association when auditing a key, so an adjacent reset
for the same mobile and room cannot falsely inherit the key. A live plan still
needs an exact carrier, class-specific HP/output proof, and a bounded item-
confirmed segment before it can be dispatched.

DD4 area `D` records use their second field as a lock type, not as a raw exit
flag bitmask. The source mirror follows `db.c`: type `2` includes
`EX_PICKPROOF`, while `-1` and `0` leave the exit open/default. A source route
through a type-2 door must remain rejected even when the character has positive
`pick lock` practice. The Dwarven Catacombs sanctuary plan now uses the
separately source-proven key 6502 on guard 6500 in rooms 6505 and 6540; its
live maintenance gate still requires exact source identity, isolation,
consider, and corpse-confirmed key extraction before `unlock west`. Each room
has two raw M resets for source mobile 6500 and each reset has a maximum-count
of four. The source route checks 6505, makes one `east east west west` detour
to 6540, and returns to 6505 before unlocking. It still requires passive
source profiles, known selectors, a source-derived joiner defense, and no
extra or unknown mobile. Revisions 313 and 314 reopen their exact same-boot artifacts;
315 recovers the old selector-persistence acquisition, 316 reopens only the
matching reconnect loss, and 317 records the alternate-room route. Revision
318 conservatively required sanctuary because same-prototype guards can join
a fight. DD4 `fight.c` limits assistance to mobiles within three levels below
through six levels above the player, and also prevents good-aligned mobs from
joining a fight against a good-aligned player. Mobile 6500 loads at level 20
with at most two levels of fuzz and has good alignment. The campaign uses
DD4's level and alignment assist checks to choose the needed defense: a guard
that could join requires sanctuary, while a known-good player who prevents the
join must still be confirmed good at the live gate. Missing source identity
fails closed. At level 30 the source level ceiling alone rules out assistance,
so neither sanctuary nor good alignment blocks Dorrik's key route.
Exact live selector, isolation, consider, the 90% route-gate health floor,
corpse-confirmed key extraction, and all other route checks remain mandatory.
The source proof also requires the key on the first same-room guard reset. When
the duplicate guards are otherwise indistinguishable, the route prefers the
lowest runtime target ID first; this is only a search order, never proof that a
guard carries the key. Inventory/corpse confirmation remains authoritative.
This gate grants no progression XP permission. At the exact level-25 frontier, source mobile 2011 is the only admitted transit special: its
level-15 upper bound is exactly ten levels below the player, its
`spec_cast_mage` acts only after combat begins, and its source damage bounds
fit the player ceiling. The live route must confirm that VNUM through GMCP;
the interruption is bounded maintenance combat and never progression XP.

October 12 NZST live run **17571** reached Dwarven Kingdom room **6505** and
used the area-scoped `where dwarf guard`. It listed six guards at **Door to
Kingdom** (room **6509**) and none at the key-route rooms 6505 or 6540. The
source `M 0 6500 6 6509` reset groups equip gear but do not load key 6502; the
key-bearing resets are the separate groups at 6505 and 6540. This snapshot does
not satisfy the route's key-carrier gate, and the level-20 guards at 6509 are
below-band for Dorrik 37. Do not fight them for XP or reopen the failed route
from this evidence. The probe recalled, returned north to healer room 3054, and
logged out cleanly without combat.

If the Dwarven route reaches room 6505 and west remains locked after the
registered open-door recovery, record a same-level, same-boot key-gate failure
and do not dispatch that route again without new evidence. A later live
inventory containing the deep green key reopens the route; a level or reboot
change also invalidates the old blocker. Startup repair may recover this
blocker only from the matching linked, successful, safe segment with the exact
locked-exit evidence and no objective kill.

The route-gate loot handoff is source-aware: after each exact guard kill it
checks the guard corpse for the source-loaded deep green key before sacrificing
the corpse. The controller records gate kills as maintenance, never progression
XP. One startup revalidation is allowed for the earlier current-level,
same-boot ``locked after open`` result that predates this handoff fix; it
preserves the old segment and consumes the fresh marker before dispatch. A
different route failure, missing source identity, or another locked-door result
does not reopen the route.

Revision 340 is a narrow implementation revalidation, not a general retry:
only the exact revision-339 fatal result and its linked successful, safe,
no-objective-kill segment qualify, with unchanged boot, level, source revision,
XP, XP-loss totals, no carried key, and full-health healer start/end checkpoints.
The route must have stopped on the exact closed-then-locked west-door hazards.
The migration preserves the old result and marker, loss quarantines, and
sanctuary/reset counters, while clearing only this route quarantine and old
selector ordering. Consume the one-shot marker before dispatch. A route failure
or interruption after that point does not authorize another attempt; fresh
live identity, room-wide isolation, consider, health, sanctuary, and route
gates remain mandatory.

The same area also resets object **6502** on mobile **6502**, the wraith in
room **6527**. Do not treat this as an independent key source: the source
route to room 6527 crosses the locked west exit from room 6505, which itself
requires object 6502. The Grand Templar carrying sanctuary flask 2008 in room
2025 is behind that same key dependency. This is source-map evidence, not a
live acquisition result; the level-aware guarded key gate remains
authoritative.

TARGETMODE selectors identify live mobile instances, not durable characters.
Keep attempted gate selectors within the connected encounter; campaign history
may retain them for audit but must not seed a later run. DD4's name-only
`Char.Enemies` update must preserve the exact active gate selector only while
that selector remains in the current room listing. If it is absent, fail closed
instead of switching to another same-name mobile.

Revision **282** adds one narrow funding exception for this plan. If a level-24+
Thief still needs the 1,000-copper source lockpick, the selector may choose
only Shargugh (mobile **6115**, room **6100**) and its source-reset iron ring
object **6114**. The route is bounded at 12 commands and 56 movement and must
issue the source `where drunk` preflight; exact mobile, room, object, one-spawn,
HP, output, capacity, inventory, route-hazard, and safe-sale checks remain
mandatory. The ring expedition is a maintenance/funding objective, so its XP
must not enter progression evidence. Source value is only a floor: verify the
actual post-reboot sale price before buying the lockpick, and checkpoint any
purchase failure as live evidence.

If that lockpick marker is active after the exact Shargugh attempt is absent,
the campaign must retain the `provision-funding` handoff while it evaluates
other candidates; a generic exhausted source frontier must not silently replace
an actionable maintenance policy with an unavailable hunt. When a known copper
shortfall is present, rank only candidates that already pass the ordinary
funding gates and prefer audited coin carriers whose contained currency covers
the shortfall. This preference never bypasses route attackers, sanctuary,
movement, output, identity, saleability, or below-band admission rules. An
insufficient carrier can remain a bounded fallback only when no sufficient
source-safe candidate is eligible, and its XP remains maintenance evidence.

When an active food, flight, or lockpick shortfall reaches the selector, an
excluded `empty-money-container`, `sell-loot`, or other city-maintenance result
must not erase it by becoming a generic unavailable source frontier. The
campaign may preserve `provision-funding` only from a fed, alive, non-combat
checkpoint; candidate selection still runs before connection and retains all
source identity, route, movement, protection, output, saleability, and
below-band rules. If no eligible carrier exists, checkpoint the bounded
unavailable result and wait for new source or reboot evidence rather than
repeating the connection.

If a current-reboot flight-funding attempt has just reported its target absent,
the character is at the healer, is fed and healthy, protection recovery is
required, and the sanctuary recovery budget is terminal for that reboot, rotate
to the existing source-output-gated ordinary current-band selector instead of
reopening the empty target or an older reusable funding carrier. This is a
single bounded frontier decision: sanctuary-required, route-hazard, output,
consider, and live-identity gates remain authoritative. If no ordinary target
passes them, checkpoint without opening gameplay; do not convert a below-band
funding kill into progression XP.

When no source-safe funding carrier remains and the exact same-boot ground
probe (including its one pending expanded locator search) is recorded absent,
the campaign may use the existing three-attempt current-band XP budget to
select another no-flight ground target. A pending exact locator retry takes
priority; each alternate still passes the ordinary level, output, protection,
route, consider, and live-identity gates. Persist and spend the budget per
segment, then return to funding selection. Do not repeat the absent target or
wait for a reboot while another eligible ground target remains.

Revision **322** adds the preceding bounded branch for the nonterminal case:
when a current-boot flight-funding carrier is absent and protection recovery
still has a remaining sanctuary attempt, select one source-validated sanctuary
carrier before reopening the empty funding route. The branch requires the
healer checkpoint, food, no combat, no sanctuary reserve, and the ordinary
source, movement, capacity, and unarmed-carrier gates. If the source selector
finds no safe carrier, keep the funding marker and use the existing finite
reset-wait path; do not manufacture a route or grant XP permission.

Reset repair must not erase that absent-target evidence before the next policy
selection. For the exact protection-starved, sanctuary-exhausted flight
funding state, retain the current-boot absent marker while clearing the
transient attempt list. This prevents the same empty carrier from being
reopened immediately after an area-reset wait; it does not authorize a
different carrier or bypass the ordinary source-ranked output, route,
movement, consider, and identity gates. Other funding states keep the normal
reset behavior and may become selectable again only through their recorded
reset evidence.

If the active lockpick marker remains below its recorded source cost while a
pending flight retry causes the generic policy layer to select `buy-flight` or
`buy-optional-flight`, preserve `provision-funding` before entering fame or
generic source fallback. This is a priority rule only: the character must still
be fed, alive, out of combat, and at the healer checkpoint, and the existing
funding selector must reapply every source identity, route, movement,
protection, output, saleability, and below-band gate. Do not claim progress from
the resulting funding kill; if no eligible carrier remains, checkpoint the
bounded maintenance boundary instead of retrying the refused service.

The starter runner must set `emergency_provision_sale` from the observed food
ledger, not from the existence of a stale funding marker alone. A fed checkpoint
must not enter `needs_food` or create a resupply detour; a foodless funding
marker still preserves emergency sale mode until provisions are obtained.

When a source-verified sanctuary potion is loose in inventory and a current
protection marker is active, select `audit-combat-pouch` before money-container
cleanup or field funding. Require the live pouch placement acknowledgement and
verify the worn-pouch ledger before reopening combat. Loose inventory evidence
may explain the reserve, but it does not substitute for a verified pouch
reserve at a field-fight admission gate.

When an exact source hunt stop completes below the useful-XP band, retain its
source mobile VNUM and source policy ID in the kill evidence even though
`objective_eligible` is false. Provenance makes maintenance evidence auditable;
it does not authorize another low-value fight, reopen a closed route, or promote
the XP to progression. Unknown or intercepted below-band kills keep their
existing incidental-evidence rules.

### Target-Specific Combat Output Revalidation

When a same-level source-ranked target produces one exact live HP-budget loss,
persist the target name, mobile VNUM, endpoint room, reboot, source revision,
observed GMCP maximum HP, prior audited output ceiling, and primary weapon.
Only a strictly stronger audited output that covers that exact observed HP may
reopen the same plain, autonomous-safe, current-band target. The ordinary
route, movement, funding, protection, and live identity gates still apply;
special, armed, scripted, equipped, hard-hazard, coin, and food targets remain
closed. Consume a dedicated marker at source-hunt segment start, after all
preparation has selected the target. An interrupted or failed retry is closed
for the current reboot and level, and source revision synchronization clears
the evidence. This contract is a bounded live measurement, not permission for
general target expansion or an unlimited fight.

### Route-Only Loss Revalidation

An exact same-level, same-reboot source-ranked loss may be reopened once when
the saved segment proves the loss occurred before target combat: the target was
not present, no consider or objective-kill evidence exists, the character ended
at least 90% healed, and the sole route hazard is a source-labelled below-band
transit interruption. The exact policy and source revision must match a fresh
current-band candidate that remains autonomous-safe and passes the ordinary
source, identity, HP, output, movement, route-program, and crowd gates.

Repair legacy segment evidence before arming the marker. Persist the marker and
consume it at segment start, after preparation has selected the target. A
productive target result clears the route-only marker and its exact loss record;
another failed or interrupted attempt closes the marker for that boot and
level. Never use this exception for a combat loss, absent-target search, hard
route hazard, below-band progression, or a generic retry loop.

### City-Greeter Route Revalidation

The level-25 Solace Secretary fallback may receive one fresh city-route check
only when its recorded prior segment ended at healer room 3054 at full health,
with unchanged XP, no combat or kills, and the exact source-registered Drunk
preflight at Temple Square. Match the same source mobile, reset room, boot, and
level; retain the ordinary no-sanctuary output and route gates. From recall,
issue a fresh `where drunk` and reject any selected route that crosses a
reported location. Consume the marker at dispatch. This reopens navigation
only: live identity, consider, and damage gates still control combat, and any
combat loss closes the policy for that boot.

## Capacity And Worker Recovery

Reconstruct pending capacity-container metadata chronologically from successful
or ready segment end states. A later explicit vault claim must suppress stale
legacy restore evidence, while a carried sack, backpack, or girdle is removed
from the pending list. If a live claim is rejected for weight, allow one
healer-side equipment-relief pass and one retry; retain the normal recovery,
funding, and bounded-retry gates.

Required-loot routes must declare their missing objects before departure so the
healer capacity controller can free a bounded number of slots safely. The
Vampire Catacombs exhibition ticket is one such required object: its live
purchase may fail for capacity even when the character can afford it. Record
that outcome separately; only an exact live funds refusal may open the
Catacombs funding handoff. A carrying refusal is never evidence of a money
shortage.

When a bounded worker is interrupted, preserve its evidence and let the next
startup recover the prior run before opening new live work. Stop only the
abandoned DD4 worker or diagnostic process after its deadline; leave the healthy
Discord streamer and unrelated services untouched.
On the shared multi-character database, use the indexed scoped recovery command
(`recover-runs --campaign-id ID --character NAME`) after verifying the worker is
gone; the global no-argument recovery scan is reserved for small databases.

## Healer-Side Deity Prayer

DD4's `deity.c` allows `pray protection` only when the level-15-or-higher
character's patron offers it; peaceful and lawful patrons include that prayer,
but the patron's stature determines which effects it grants. Never infer
sanctuary from the command or patron name. When a selected current-band hunt
needs sanctuary and no durable reserve exists, the campaign may try one prayer
from healer room 3054 per DD4 boot. Require a live, safe, provisioned healer
checkpoint; wake at most once, issue exactly one `pray protection`, then save
and quit. Consume the marker before dispatch. A recorded command spends the
attempt even if the patron refuses or the favor/timer prevents a grant; a
bounded pre-login failure with no prayer command does not. Only a fresh
sanctuary affect in the saved GMCP state can help selection, and every ordinary
route, identity, consider, output, and survival gate still applies. Live
success remains unproved until the affect is observed after the prayer.

If the ordinary source selector rejects a current-band target solely because
the missing reserve blocks its output admission, it may expose that exact
source-ranked candidate only to choose the healer prayer policy. The candidate
is removed before dispatch; this exception authorizes no route or combat. After
the prayer, selection starts fresh and every ordinary source and live gate is
applied again.

If the MUD reports that the character has no patron, the command still spends
the boot's one-shot attempt. Do not automatically follow it with `pray
patronage`: DD4 warns that patronage may be difficult to leave, requires
multiple confirmations, and may not grant the required protection. First
verify the exact patron's prayer list and character-specific favour from
source/live evidence. Dorrik's October 9 attempt (run 16571) returned “You have
no patron,” granted no Sanctuary, and left him safely at healer room 3054.

The same recovery rule applies to an emergency no-recall escape. A generic
source-ranked candidate is dispatchable only when source data proves either a
direct return route or a replayed reverse of the audited outbound route; the
outbound commands themselves are never a return plan. At the Ice Hall, take the
source-verified open exit to the recallable room only when live flight, water
travel, or another source-supported movement capability is present; otherwise
consider prayer.
Issue `bash west` only when the live skill audit shows a usable `bash door`
skill. If an already-known Rescue prayer produces only the ordinary prayer
response, do not select a patron or treat the acknowledgement as movement. Keep
the character in the exact source-verified room, repair hunger/thirst from
carried supplies, sleep, and retry Rescue at one-minute intervals while reading
live output; DD4's source cap makes this a maximum six-hour connected wait. If
a needed food or water supply is absent, this exact no-combat room may still
sleep through the wait because the source clamps a starvation or dehydration
hit that would cross zero, but the damage can still reduce health sharply. If
health falls below 25%, wake and use a learned cure spell when the normal mana
reserve allows it, capped at three casts before returning to sleep. Keep the
live health, room, and no-combat checks active. Stop on a room change,
combat/death, a broken live health/room boundary, or the bounded deadline.
If the patron offers Transport but not Rescue, use it only for the
source-registered Midgaard healer mobile **3012** in room **3054**. A refusal
or missing target closes that exact fallback and is preserved as live evidence.
This is a recovery exception for the exact Ice Hall route, not permission for
generic timer waits or offline retry quotas.

## Mirror Realm Route Recheck

Run **17554** reached Mirror Realm room **19056**, Foot of the Rock Ladder. The
live exits were a closed west door and up, but the registered Jerry Garcia
route issued another `down`, received `Alas, you cannot go that way.`, and
recalled without combat. The first route correction was short by one descent:
run **17555** reached room **19044**, Below the Watchtower, then tried west
although its exits were up and down. The source graph and run 17554's room
sequence show the path needs two downs after entering the watchtower, reaching
room **19045** before opening west. Preserve both failed segments and use the
distinct `mirror-realm-jerry-garcia-route-recheck-v2-36-40` policy for one
final no-combat route check. Run **17565** consumed that policy but did not
leave healer room **3054**: its three bounded `where drunk` checks ended with
the field-city preflight blocked, without movement, XP change, or loss. Run
**17566** was a separate eight-command world-time/locator check at the healer;
it observed three city locations instead of none. Both runs used source
revision `2533108641f46f7a6998d3ac4ec54c0f47194e8d`, while the current parsed
source is `9205f31648e713953edb77f844325fa47b6fd9bf`. The level-37 city-clear
revalidation was already consumed for the exact Lotus Temple policy
`source-ranked-hunt-lotus-temple-10736-10837-37`; do not transfer it to Mirror
Realm. These records do not prove the Mirror route clear or authorize a route
or combat retry. Any distinct source-refresh revalidation must satisfy its
exact registered policy and all ordinary live gates.

Source audit correction: Mirror Realm mobile **19004** is Caerlin, level **35**.
His reset in room **19068** equips the **Staff of the Bard** (**19173**) in
the hold slot and also loads a silver harp (**19011**); object 19173 is a
10-charge staff whose source spell is `sanctuary`. This makes Caerlin a valid
Sanctuary-resource target, not a safe or plain XP target. His
`spec_cast_cleric` special only selects someone already fighting him, then
casts offensive spells including blindness, curse, flamestrike, harm, and
dispel evil. Require exact live identity and consider, a source-bounded combat
plan, and verified acquisition/brandish before counting Sanctuary as a reserve.
Do not confuse it with the separate Royal Staff (**19010**) equipped by the
withered knight (**19012**) in room **19043**; that staff casts `heal`.

Run **18010** followed the official recall route through room **19008** and
received two live `where Caerlin` replies naming “Beside the Watchtowers”; the
mobile had moved before the later room inspections. The reset-room endpoint
**19068** has no source-safe reverse route to **19008**, so the generic local
locator cannot recover that sighting. The bounded recall-origin prefix
`mirror realm caerlin watchtowers` ends at **19008** and is for exact live
consideration only. It does not lower Caerlin's special, output, isolation,
recovery, or combat gates.

The current carrier executor starts at the exact reset room with a live `where
caerlin` locator. If Caerlin wanders into an already-checked room or outside the
audited relocation graph, one safe, no-loss retry may be consumed after the
positive locator evidence is checkpointed. A second miss closes this recovery
attempt until the normal source/reboot evidence changes; it never authorizes a
generic chase or combat outside the registered route.

Run **18490** added a distinct live observation: Caerlin was visible in room
**19002**, “The Path,” while Dorrik was still following the official outbound
route to room 19068. The generic locator must continue to reject that ambiguous
label, but the exact source VNUM and route prove this one waypoint. The carrier
stop now permits one outbound interception at VNUM 19002 only; it still requires
the live source identity, isolation, consider, output, required staff receipt,
and healer-return checks. The current boot's retry is already closed, so this
evidence will be used on the next eligible recovery attempt rather than looped.

If an exact Caerlin dispatch reaches field combat and aborts without acquiring
the staff, startup reconciliation closes that attempt as
`combat_aborted_no_acquisition`. It does not classify the result as a locator
miss or spend the one safe locator retry; only the documented positive-where
miss can open that retry.

The next source-ranked Sanctuary fallback is recorded as
`source-ranked-sanctuary-alternate-2-100`. Its first eligible carrier is the
level-39 Alchemist (mobile **916**, room **927**), whose source reset can load
the ivory staff (**905**) and nectar (**926**) and has no listed special. The
selector binds the effect, reset, route, isolation, and output evidence rather
than assuming a mobile name. The ordinary Alchemist hunt already recorded an
absence on the current boot, so this fallback remains closed until a reboot or
source revision changes that evidence; it is required-loot maintenance, not XP
permission. A legacy absence without a complete boot boundary is also kept
closed, because it cannot prove either current-reboot absence or post-reboot
availability.

October 13 NZST run **17722** reached Jerry Garcia's registered endpoint and
refreshed `where` once; the live result located him only at “Below the
Watchtower.” The current source map identifies that label as room **19044**,
but it is outside the route's registered source-safe relocation graph. The
probe returned to healer room **3054** and logged out safely without combat or
XP. Preserve the locator evidence, but do not follow or fight there until an
audited safe approach is registered.

Dorrik's level-37 skill audit is historical; the current level-38 proficiency,
practice, and trainer audit is recorded above. Keep the same Warrior/Knight
source priorities, but re-evaluate their useful targets and actual lesson access
against the current live balance and exact teacher before travelling. Recheck
on the next level, practice gain, new unlock, or relevant source change; do not
repeat an unchanged trainer visit.
At a fresh trainer listing, compare the current proficiency, useful target,
remaining practice balance, teacher cap, and level-up HP/mana value. Refresh the
listing after an accepted lesson and continue high-value training when another
source-supported gain is worthwhile; do not mistake an initial unlock for a
finished skill. Preserve practices when no useful teacher-supported lesson
remains.

## Current Level-39 Frontier (October 21)

Run **19086** was a bounded world-time probe and confirmed that the DD4 boot had
not reset. Run **19087** then used the exact source-bounded, two-to-four-reset
economic-transit exception to reach Orion, mobile **9311**, room **9328**. The
fresh two-potion Sanctuary refill, or a carried charged source Sanctuary staff
whose acquisition receipt had been compacted, permitted one exact
revalidation of the prior
unprotected loss; live identity and `consider` passed, and Dorrik killed Orion
for **3,103 XP** before returning to healer room **3054**. Run **19089** later
re-tested that productive route, passed the same fresh identity and `consider`
checks, then withdrew at the 20-percent floor after **154 incoming damage** for
a net **441 XP** loss. Checkpoint **58334** preserves that exact same-boot loss
and closes Orion for this reboot. Run **19090** completed the bounded reset wait
and world-time probe safely; the DD4 boot was unchanged and no XP was claimed.
Checkpoint **58343** preserves that result. The maintenance-only checkpoint
**58346** opened no gameplay connection and claimed no XP. The selector will not dispatch Arthur the
psionicist or any other level-40+ psionic without a fresh, source- and
live-verified disintegration-protection receipt; Sanctuary, energy containment,
or an ordinary saving throw is not enough.

## Documentation

`README.md` is current usage; `ROADMAP.md` is delivery gates. Dated reviews hold
analysis and run evidence. `docs/history/` preserves prior documents without
making their old "latest" sections authoritative. Update current facts once
in the active review rather than copying every run into all three root files.

## Level-Based Engagement (October 15)

### Consider Evidence Ownership

The live controller may keep a boolean `consider_viable` for the immediate
combat decision, but campaign history must also retain the captured MUD reply.
Only an observed result with nonempty response evidence can close a target for
the current source/boot. A legacy row that contains only the boolean is
incomplete evidence: preserve it for reporting, mark the gap, and let the
normal bounded selector re-probe the target. This prevents an interrupted or
partially recorded observation from becoming a permanent XP frontier blocker.

Choose mobs by relative level and live `consider`. Target hitpoints are
diagnostic evidence, including the health comparison in `consider`; they do
not veto a target, require sanctuary or HP gear, or trigger an escape based on
predicted damage or kill duration. The character's own health and actual
encounter hazards still govern withdrawal. Preserve exact previous loss
records; changing this strategy does not automatically retry failed targets.
