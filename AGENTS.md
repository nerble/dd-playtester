# Repository Guidelines

## Project Structure

The `dd4tester/` package contains the asyncio Telnet client, GMCP parser,
scenario runner, persistence layer, state model, and CLI. YAML scenarios live
in `scenarios/`; keep reusable scenarios small and non-destructive. Tests are
under `tests/`, with sanitized protocol samples in `tests/fixtures/`. Generated
SQLite databases and JSONL transcripts belong in `runs/` and `transcripts/`;
both directories are intentionally ignored by Git. Generated declarative HERO
requests, profiles, campaign files, and generated `hero-report.json` /
`hero-report.md` artifacts belong under `runs/heroes/`.
Each run context must retain the configured non-secret title, description, and
optional personality so reports and later commentary can recover the character
persona without reading credentials or guessing from the character name.

## Master Goal And Proof Discipline

The master objective is a character-independent engine that accepts any
source-legal race, cosmetic sex, base class, optional subclass, name, and
personality, creates or resumes the character, and plays it autonomously to
HERO level 100. Names and credentials identify stored history only; never add
name-specific behavior to make a live run succeed. Direct Telnet/GMCP is the
primary behavior adapter. Mudlet and Windows VM automation are separate
visibility and lifecycle validation boundaries. AI decision-making remains out
of scope until deterministic behavior is replayable.

### Capability Authorization

Observed skill names and percentages are durable evidence for training,
readiness, and reports, not permission to issue arbitrary commands. Live
dispatch must use the source-audited class/subclass registry and then apply
the action's own positive-practice, equipment, resource, target, and safety
gates. When an observed skill is missing from the registry, preserve it for
audit and add source/formula/runtime tests before making it executable; never
let a stale checkpoint turn an unknown name into a live action.

## Strategy And Runtime Priorities

Run `python -m dd4tester autonomy-audit --race ... --sex ... --class ...` or
`python -m dd4tester autonomy-audit --race ... --sex ... --all-classes` when
inspecting coverage. This is a static template/status inventory, not proof that
every character can execute the registered path. It reports combat automation
status and declared gaps separately from training priorities; a skill listed at
`0%` is not an executable capability. Choose engineering work from actual
current character levels and failed/live outcomes; the audit's first declared
gap must not reset an already advanced character's frontier. Follow
`docs/REASSESSMENT_2026-09-05.md`: measure net XP per elapsed time including
maintenance, improve trained damage/protection and multikill journeys, and
extend policy bands in step with live characters.

Authenticated Purgatory recovery must preempt stale route, acknowledgement,
and logout work. Shared combat survival limits must run before route-specific
combat, including below-band transit fights. Preserve source-gated finishing
attacks and usable healing reserves; do not globally raise flee thresholds to
repair an ordering bug. Telnet GMCP can duplicate the primary opponent while
another mobile attacks: corroborating combat text must prevent false isolation,
while duplicates alone and source-known harmless bystanders remain tolerated.
Outer-timeout results must checkpoint the latest run snapshot and retain failed
status, never reuse an old healthy snapshot or inherited objective kills.

Generic route preparation consumes capabilities, with source-legal, trained,
and currently usable states distinguished. Validate spell upgrades from live
practice listings before casting them. Preserve current trainer limits and
practice budgets, and add cross-class replay tests for shared runtime changes.
The runtime must apply the same positive-proficiency rule to openers,
mitigation, between-round attacks, and subclass actions. Keep the all-class
audit honest: registered templates and declared gaps are planning data until
replay-backed live evidence proves a class or subclass route.

Source-ranked combat may use `SourceCombatOutput` only for formulas audited in
the checked-in DD4 source. The conservative action budget, source expected
incoming-round estimate, incoming-peak ratio, health reserve, and mana reserve
are admission gates for a bounded live probe, not progression proof. Carry the
action and source reference into `FieldHuntStop`; at runtime, require a
current-room enemy HP snapshot when the source HP ceiling exceeds the player's
max HP, then retain live `consider`, health, crowd, resource, and damage-window
gates. A live projection that cannot preserve the field reserve must quarantine
the route after the bounded withdrawal. Unmodeled physical output remains
unassessed and must not be admitted by a guessed damage value. Action-budgeted
output does not require a caster mana reserve, but it still consumes the live
between-round cooldown.
Mobile source ranks are executable safety data: parse the area-file rank
record and apply DD4's `mob.c` HP multiplier when estimating a target. Keep the
rank in candidate output and checkpoint records so an elite, boss, or world
mobile cannot silently resume as a common target.
Direct damage action ordering is defined once in
`dd4tester/combat_capabilities.py` and consumed by both source ranking and
`StarterPolicy`. Keep source references and the `estimated` flag accurate:
adding a runtime command without a checked formula must remain readiness-only,
while a formula without a live command is not executable capability. Update
the corresponding training priority and focused contract tests together.
The source-backed control-only `disarm` action is registered for thief,
warrior, ranger, and vampire identities with `estimated: false`. The live
controller may use it only with an observed player weapon and its bounded
response handling; registry visibility must not turn it into damage output or
authorize it for an unrelated class.
The current source-audited direct spells include `harm` for necromancer,
`wither` for druid, `flamestrike` for knight, and `agitation` for psionic or
monk, plus action-budgeted `atemi` for martial artists and
`wolfbite`/`ravage` for werewolves. Base brawler `punch` is also modeled.
Martial-artist `kansetsu` is controller-ready only as a one-shot, source-gated
weapon-arm disarm: require positive live proficiency, an exact fresh source
target, and source evidence that the target is armed; consume the attempt on
any server response and do not add its damage to source estimates until target
weapon state is observed and calibrated.
Preserve DD4 mobile body-form bits from the area parser through candidate,
checkpoint, and field-stop state. Treat `None` as missing legacy evidence and
parsed `0` as meaningful ordinary anatomy. Kansetsu additionally requires
known usable arms. Thug `smash` requires a known non-huge source target, a
worn shield, an awake fighting state, and the same exact live-target gates;
never infer either fact from a mobile name or from a stale synthetic record.
When a brawler has a positive observed `second punch` proficiency, include its
automatic roll in the `punch` damage budget; do not issue a separate command
or assume the roll when the proficiency is unknown.
The source-backed `headbutt` action is executable for warrior, brawler, and
barbarian identities only when positive proficiency, fighting position, exact
live target identity, and parsed body-form flags prove a non-huge target has a
head. Include DD4's optional `second headbutt` and automatic weapon cycle in
the estimate; issue the exact no-argument command only once per fresh live
between-round decision. Unknown anatomy, head trauma, stale target snapshots,
or non-fighting state must remain unassessed rather than guessed.
For thief backstab projections, include DD4's automatic `double backstab`
branch only when its positive live proficiency is observed; it is part of the
one-shot opening budget, never a recurring action or a separate command.
Thief `trip` and `dirt kick` are control-only capabilities: dispatch each at
most once per exact source target, require known source anatomy and a fresh
GMCP enemy snapshot, and reject incompatible sectors or confirmed transient
target states. Keep them out of source damage estimates until those state and
sector inputs are modeled. The player-facing `dirt kick` skill maps to the
source prerequisite graph's internal `dirt` symbol through `source_skill`.
Pass both base class and live subclass to the estimator; never let a spell or
skill learned by one subclass authorize another subclass's route. These
formulas remain bounded probe evidence, not proof of a live kill.

The werewolf controller may issue `morph wolf` only from an observed normal
form, with positive observed `morph` and `wolf form` proficiency and at least
100 mana, matching `sft.c` and the `wolf form` minimum-mana table. It then
issues `wolfbite` or `ravage` only from an observed wolf/direwolf form. Form
equipment changes are live state, so no static form estimate may bypass the
ordinary equipment, target, health, or return gates.

The straight-shifter controller may issue `morph snake` only from an observed
normal form with live-known `morph` and `snake form`, observed form proficiency
at least 20%, and the source-calculated form mana cost. It is a lifecycle
fallback, not a natural-weapon damage estimate. A returning straight shifter
must restore normal form in healer room 3054 before equipment or sale work;
unknown or subclass-specific forms remain untouched until their own policy is
audited.

## Documentation Synchronization

When a CLI command, output format, storage path, credential flow, runtime
limit, or operator workflow changes, update `README.md` in the same work unit.
Keep examples runnable from the repository root, include the relevant
PowerShell commands and paths, and refresh the current test/live status without
turning checkpoints or research probes into progression claims.

New HERO workspaces must pin the resolved DD4 area directory used for both
identity validation and runtime source planning. `--source` may identify
`const.c`, its `src` directory, the server directory, or the area directory;
resumes must honor the stored pin rather than silently switching to a freshly
pulled source tree. Source loaders should use the campaign-local source scope,
not a second hard-coded default.

Connection-loss policy: Telnet connect, read, and login-inactivity retries are
finite. A bounded socket failure must persist an explicit return-home marker,
clear transient target/crowd observations, and stop the campaign rather than
retrying a field route. The next invocation must select `return-home` before
any new target; endpoint checks such as `Test-NetConnection` are diagnostics,
not progression evidence.

Long campaign invocations must remain operator-visible when requested: the
`campaign` and `hero` CLIs expose `--progress`, which reports each bounded
attempt's start and completion, checkpoint, level, and XP to stderr. Keep the
final result on stdout and preserve the same bounded segment, reset-wait, lease,
and cleanup behavior; progress output is observability, never a substitute for
durable SQLite evidence.
`run_campaign_file` also continues a multi-segment invocation after an explicit
recoverable route-hazard checkpoint, including a bounded city-shop deferral,
route quarantine, or runtime-cap resumption. It still stops for an
`awaiting_area_reset`, unavailable, blocked, or failed result, so continuation
cannot turn a reboot wait or safety boundary into a retry loop.
For capped invocations, also emit explicit markers before and after cold local
source-catalog preparation so setup latency is visible; these markers do not
consume the live segment budget or count as progression evidence.

At campaign startup, compare a character checkpoint's `world_boot_id` with the
newest reboot marker observed in the shared SQLite `runs` ledger. If the ledger
has a newer marker, schedule exactly one maintenance-only `world-time-probe`
before selecting reboot-scoped cooldowns or route evidence, including for a
bounded invocation. The shared marker only triggers revalidation; the live DD4
`time` response is the authoritative reboot proof, and the probe must never
replay a field route.

When flight funding is required but no safe funding candidate remains in the
current reboot, a stocked character may preflight one independent
source-ranked no-flight target and let the normal selector persist and dispatch
it. Preserve the flight-funding markers for a later reboot; ground fallback is
ordinary progression and never evidence that flight was acquired.

Every healer-origin Midgaard liquidation route crosses the source-identified
Temple Square room. Before any city-shop movement, apply the shared drunk
preflight: a class with a live or source-legal invisibility capability casts it
and stays invisible until the shop, while other classes issue a bounded
`where drunk` locator check before crossing. An absent, blocked, or inconclusive
locator is a maintenance boundary: remain at the healer and checkpoint rather
than walking into an unclassified greet-program hazard. Restore visibility only
at the shop. The persisted `magic_shop_route_blocked_by_drunk` marker is shared
route-hazard evidence for all healer-origin shop sales, not a magic-shop-only
flag.

The source-ranked selector must pass its loaded `WorldSource` into movement
gates. A route over the current movement pool is executable only when the
source planner proves an audited `no_mob` waypoint split; preserve the live
consider, crowd, resource, and healer-return gates after that split.

The source `show-resource-sources` report must keep direct ground resets,
mob-carried or equipped resources, and shop stock distinct. Its rows must show
the exact object VNUM, reset room, source level range, route, and source-derived
hazards. `source-only` is research evidence, not live availability or
progression proof. Successful StarterBot checkpoints persist the observed
`campaign_known_skills` and `campaign_known_skill_levels`; maintenance merges
those capabilities forward, and startup repair must reconstruct them from a
bounded history of accepted training events for legacy checkpoints and supply
them to the resumed StarterPolicy before field decisions. Every accepted
lesson must request one bounded trainer-listing refresh before another lesson or
field decision, so the durable percentage cannot lag the acknowledgement. A
trained sanctuary or cure spell may count as the corresponding executable
reserve only when the live practice listing actually observed it.
When matching a source-required object to a mobile reset, inspect both its
carried object list and its equipment placements. Keep `mob-carried` and
`mob-equipped` provenance distinct from saleable carried loot, and carry the
exact object and mobile VNUMs into the live required-loot stop. The generic
sanctuary executor may use a different source-safe potion carrier, but must
retain the proven Moria route as fallback; a key-locked or otherwise
unexecutable source placement remains `source-only`. `ResourcePlacement.activation`
records the source command contract (`quaff`, held `recite`, held `brandish`, or
held `zap self`) for castable resources. After a required object is confirmed by
live acquisition, persist its exact activation contract in
`campaign_source_resource_reserves`; the resumed StarterPolicy may then hold
and activate it, consuming the object or decrementing charges only after a live
acknowledgement. The source row alone is never reserve proof.

At level 25 and above, remote field routes may use only recall points observed
in the live `recall list`. If a source-registered point is missing and the
observed spendable quest-point balance can afford it, acquire the most valuable
missing point at the correct questmaster, refresh ownership, and restore the
default recall before healer recovery. Acquisition and remote-origin routing
remain research evidence until a fresh live run confirms both the purchase and
the return sequence.

For the public hero entry point, honor an explicit password and the process
environment before reading character:<name> from the credential store. Make
credential reads and writes bounded. Reuse an existing stored character
password before generating one. An untouched `--prepare-only` workspace may
generate and store its first password; once the shared database records a
campaign for that workspace, a missing credential is a strict resume error and
must never be replaced automatically.

Keep proof layered and honest: creation/tutorial, representative level-10
classes, executable class-aware level 1-30 coverage with confirmed subclass
transition, then bands 31-70 and 71-100, followed by fresh creation-to-HERO
runs. A checkpoint, policy-count report, source catalog entry, or research
probe is not proof of progression. Use `verified` for reusable executable
evidence, `research` for bounded probes with explicit limits, and
`unavailable` for an explicit safe stop. Every engineering work unit must
remove a concrete blocker to the next executable level band.

Source-ranked candidate inspection consumes durable class and trained-skill
state when it is available. Its `combat_readiness` label and `combat_bonus`
are deterministic tie-breaker metadata only: they may favor an executable
near-band damage action, known disarm against an armed target, or a defensive
reserve near the source peak, but they must never change a candidate's safety
status or bypass live consider, crowd, route, health, resource, and damage
window gates. Missing or legacy skill state must remain `unassessed`.
The `show-hunt-candidates` inspection command must overlay the newest named
campaign checkpoint onto the latest raw character snapshot, so durable skills,
skill percentages, subclass, and recall ownership are not lost when a live
snapshot contains only GMCP character fields.

An audited hard route preflight hazard is never waived because its source level
is below the ordinary XP band. Shadow Guardians are the concrete example:
their source level is low, but their special damage can still make a transit
route unsafe. Preflight must stop before the waypoint, persist the hazard, and
quarantine the route for the current reboot. After a successful emergency flee,
discard stale GMCP enemy state and enter the bounded return path directly;
never issue a second flee from the same stale snapshot. `Char.Enemies` is also
room-scoped: invalidate it on an observed room transition and trust it again
only after a fresh snapshot for the current room. Combat flags and explicit
attacker text remain authoritative when a packet-ordering gap exists.

Direct food and coin stashes may carry one source-identified probabilistic
program attacker as a route-origin `where` preflight. Compare its normalized
live locations with the normalized source room names crossed by the route;
continue only when it is off-route. A present target or an inconclusive locator
is a hard return-home boundary. Deterministic program attackers and multiple
unresolved program attackers remain source rejections. Preserve this metadata
through candidate serialization and every generated `Fastwalk` route.

Equipment planning must distinguish worn gear from usable held resources. DD4
potions (`ITEM_POTION`), food (`ITEM_FOOD`), and drink containers
(`ITEM_DRINK_CONTAINER`) can be holdable objects, but they are not wear-slot
gear; exclude them from equipment audits while retaining them for consumption,
water, and emergency-combat planning. Recovery score probes may remain while
sleeping; only commands that require an awake position should wake the
character, and Midgaard healer recovery belongs in room 3054.

Source combat output may include ordinary weapon strikes only when the current
structured equipment snapshot, or an unambiguous legacy checkpoint, identifies
the primary `WEAR_WIELD` source object. Apply the source object's `one_hit` damage range,
live damroll, observed enhancement percentages, and conditional `multi_hit`
follow-up chances. Hit chance, temporary affects, target armor, and resistances
remain live evidence; an unknown or ambiguous weapon must stay `unassessed`.
Carry the source reference into the field stop and preserve the existing live
consider, health, resource, route, and damage-window gates.
The same output contract covers the deterministic between-round `kick` and
`knife toss` actions, weighting their source level roll by the observed skill
percentage. `knife toss` must be issued with its complete registered command
name; the shorthand `knife` is not a DD4 command and must never be emitted by
the controller. `circle` and `backstab` require the observed primary source
weapon whose damage type is
2 (`stab`) or 11 (`pierce`), and applies its source 1.5x damage modifier plus
the observed `second circle` chance. A trained thief's source-matched
`backstab` may contribute once to the opening budget, with its source
proficiency and multiplier, but must never be treated as a recurring damage
action. These estimates are planning metadata, not kill proof; keep live
target HP, hit chance, temporary state, and damage-window checks authoritative.
Ranger `shoot` is a one-shot opening: require a structured source-identified
`ranged_weapon` slot and weight its one-to-three `one_hit` volley by observed
`shoot`, `second shot`, and `third shot` proficiency. Do not treat the bow as
the primary melee weapon or as recurring damage; keep the opening budget
separate from the normal weapon or kick action.
Vampire `lunge` is a one-shot opening only. Its source estimate must mirror
`fight.c:do_lunge` and the `gsn_lunge` branch in `one_hit`, including the
half-damage and rage adjustments and a second bounded `multi_hit` only when
positive `double lunge` proficiency was observed. Live dispatch requires the
source-ranked stop, a fresh unique `Char.Enemies` target at full HP, and no
existing fight; a source rejection sets a one-use skip marker and falls back
to ordinary combat. Never issue lunge against a wounded, ambiguous, or already
engaged target, and never count it as a recurring between-round action.
Warrior `stun` is likewise an opener, not a damage estimate: issue it only
when live practice is positive, the source stop identifies one exact VNUM in a
fresh full-health `Char.Enemies` snapshot, and a source-matched blunt weapon is
available. After one bounded attempt, restore the best primary weapon and
issue ordinary `kill`; source rejections must fall back once, and an absent
target must be discarded rather than retried. The shared combat registry must
filter subclass capabilities by the subclass's declared base class before
they reach either source estimation or live dispatch.
For smithy `counterbalance`, a positive learned skill is not enough to add the
passive attack. Only a confirmed anvil response may persist the prepared
weapon VNUM; include DD4's `APPLY_BALANCE` chance only when the current
structured `WEAR_WIELD` object has that same VNUM. A mismatched or unknown
weapon must fall back to ordinary output, and startup repair may restore only a
completed preparation event.
Smithy `hurl` follows the same evidence discipline: register the learned
skill, but estimate or dispatch it only when the currently wielded weapon's
`EGO_ITEM_CHAINED` flag is observed from structured GMCP or DD4 `identify`
text and its VNUM is persisted in the campaign checkpoint. A missing,
mismatched, or rejected chain marker must fall back to ordinary weapon output;
never infer hurl readiness from the skill listing alone.
If a live practice listing contains a source-legal action not yet present in
the registry, preserve it for audit and training-gap reporting; do not append
it to live starter ordering. Add the source reference, formula or lifecycle
model, executor gate, and focused tests before dispatching it.

DD4's `do_quaff` extracts a potion after spell execution, including when
`spell_sanctuary` reports that the character is already affected. Debit a
verified pouch reserve before issuing the command, track the target-level
sanctuary attempt, and never issue a second sanctuary quaff while the live
Char.Affect snapshot is stale. Restore the ledgers only for explicit
non-consuming quaff refusals; the `already affected` response is consumed
object evidence. Keep the pending-command state in memory and preserve the
durable pouch audit at healer return.

Source-ranked combat must treat DD4's `consider` response "much healthier than
you" as an unsupported durability warning unless the executable stop carries
an explicit source peak-damage bound. Consider-only research probes and stops
with that source bound retain their existing behavior; a level-legal target is
not automatically a viable target when its live hit-point pool can outlast
the character's damage window.

An unarmed one-level source-ceiling probe also requires its source estimated
base-HP upper bound to fit within the character's current maximum HP before an
unprotected fight can be selected. A per-round incoming-damage bound alone is
not enough for a high-HP target that can outlast the character's damage window;
sanctuary-backed or armed paths retain their separate protection gates.

The current read-only DD4 source baseline is
`6b6624fab18a8367aaaa4f4883e12f749704e7f6` (refreshed 2026-09-05). It names
`ACT_UNDEAD` as bit 30 and marks the chapel skeleton accordingly. Preserve that
flag through `MobileSource`, candidate inspection, and checkpoint serialization,
but do not classify undead mobiles as combat hazards from that marker alone;
the current source uses it for identity and inspection, while special
procedures remain the executable risk signal. The refreshed `fight.c` also
applies resistance categories to ordinary weapon attacks and suppresses
immunity-blocked trip/disarm attempts; keep those as source-audited planning
metadata and continue requiring live combat evidence for target resistance.

A source-identified mobile with a source-audited transit-hazard procedure is a
hard route hazard even when it is not flagged aggressive or running an attack
program. The current transit hazards are direct out-of-combat attackers,
economic theft, and unknown procedures; preserve the source classification for
all 62 special names found in the area files. Combat-only procedures may be
crossed while no fight is underway, conditional guards are safe for an ordinary
unflagged character, and an aggressive mobile carrying a combat-only procedure
remains hazardous because its normal attack can start that procedure. Target
rooms still apply the separate live isolation, consider, protection, and
special-procedure gates. Plain below-band aggressive bystanders on ordinary XP
routes retain the existing DD4 cutoff and tolerance rules, but a target's
source-fuzzed level still triggers the exact `target is aggressive` rejection
gate.

Policy revision 190 adds a repeatability guard for stale source-ranked results:
after one current-reboot XP loss, a route may repeat only with a carried
sanctuary reserve; after a second loss, it stays quarantined for that reboot.
This guard is evidence hygiene as well as safety control, and must not be
bypassed by a stale positive research result or a generic retry. It also keeps
the class-tagged warrior Mahn-Tor continuation ahead of generic level-16
research once its prerequisite evidence exists.
The CampaignRunner also preserves that class-tagged continuation after a
generic research miss when the sanctuary reserve is executable; without the
reserve, the protection gate still blocks combat at the level that incurred
the withdrawal and allows only bounded recovery or research work. When the
character advances, retain the marker for audit but do not let that older
level's unavailable sanctuary route freeze the new level frontier.
The sanctuary resource route itself is quarantined after two failed
same-reboot attempts, preventing a persistent recovery hazard from replaying
indefinitely. Run 11702 live-validated the continuation selection and its
425-XP Mahn-Tor result after the level-16 generic frontier was exhausted.
The attempt counter is durable evidence: startup repair must reconstruct a
terminal sanctuary result when a legacy checkpoint retains the two-attempt
counter but omits the result payload, so the selector cannot reopen the same
exhausted route. The terminal result must still preserve the normal bounded
independent recovery fallback.
Terminal same-reboot sanctuary failures must survive reset-wait aging; only a
new reboot or successful acquisition may reopen an exhausted resource route.
Durable source-ranked capacity history is ordered evidence: a later objective
kill reopens that source mobile after an older no-kill capacity probe, while a
newer failed probe can quarantine it again. Reuse still requires exact live
isolation, consider, route, health, resource, and healer-return gates.
A clean isolated, unarmed source-ranked target that reaches a bounded runtime
cap with negative XP but ends above 90% health may receive one exact retry when
strict source peak and critical bounds fit the current HP ceiling. Persist the
entitlement in campaign state, consume it before the segment opens, and never
let it bypass live target, consider, crowd, route, resource, or healer-return
gates. Startup may re-arm only a legacy segment that aborted before combat
because the old runner incorrectly required sanctuary; preserve that segment
as evidence and do not retry a genuine combat loss or a second timeout.
Static research hunts with armed targets must carry the same sanctuary reserve
requirement before combat; a static policy must not bypass the candidate-level
armed-target gate. A controlled runtime cap must build its checkpoint from the
fresh live character snapshot and terminal event, not by merging the previous
checkpoint wholesale. Clear transient objective-kill fields before each new
segment. During startup repair, when a segment has a run id, prefer its
terminal objective-kill event or durable `mob_kills` rows over the segment
end-state; inherited kill metadata must never hide an XP loss or promote a
failed hunt.
For the armed Lord Doom hunt, sanctuary expiry must still be evaluated against
the live matchup rather than triggering an unconditional flee: the policy uses
a 40% combat-health floor, but may take one bounded finishing action when the
opponent is nearly defeated and the live damage reserve covers that exchange.
When the current observed flight price is unaffordable, food is secure, source
funding and no-flight fallback have no executable candidate, the shop route is
not blocked, and no loan was attempted, use one bounded bank-loan handoff
before repeating empty funding hunts. Preserve the loan marker and never
repeat that handoff in the same campaign and reboot.
The emergency provision selector suppresses its city-sale shortcut while the
shared shop hazard is active. A foodless character therefore stays in the
explicit provision-funding loop, where capacity relief is applied before the
source-ranked funding route; it must not fall through to ordinary hunting
without food. Run 11639 live-validated the bounded `donate dark` relief and
safe healer return, and run 11640 bought a big pot pie at the Bakery.
Capacity relief may also release a source-identified item that the current
class cannot legally use, even when that item has otherwise sale-protected
stats (for example, a bow carried by a warrior). Usable weapons and useful
stat gear remain protected. Runs 11815-11817 live-validated this boundary,
including the resulting pie purchase and healer return.
The optional-flight branch must honor the shared
`magic_shop_route_blocked_by_drunk` cooldown as well, so an affordable flight
purchase cannot reopen a known unsafe healer-origin shop crossing. The focused
regression keeps the ground source-ranked route selected until that hazard
ages or a fresh reboot clears it.

Policy revision 193 makes the generic source-ranked frontier the first choice
for ordinary fresh research from level 10 onward. This is a fallback-aware
handoff: if the source selector finds no executable current-band candidate, the
original named research probe still runs. Dedicated resource, class/shared
evidence, quest, trainer, subclass, equipment, funding, flight, and recovery
transitions retain priority. Registered level bands remain first-class bounded
research and executable routes, and the later level-21 dynamic fallback still
prevents the static registry from becoming a progression ceiling. All live
target, consider, crowd, route, health, resource, damage-window, and
healer-return gates still apply.

Transit risk is wider than the ordinary XP cutoff: an aggressive source mobile
whose maximum fuzzed level is within 10 levels below the character blocks a
route even when it is not a useful XP target. Keep the ordinary five-level XP
cutoff for farming decisions, but apply this transit band to fixed-reset route
hazards and source-reachable aggressive wanderers. A below-band room companion
with an attack program is also non-trivial because `greet_prog` or similar code
can initiate combat. Before any long class-trainer trip, preflight the source
route from healer room 3054. If the route is blocked, defer training, persist
the exact hazard, and remain at the healer rather than discovering it after a
flee loss.

During active current-reboot protection recovery, an unprotected HP-fuzz
durability probe is sanctuary-gated even when its source peak fits the narrow
probe budget. The separately audited plain-target fallback may proceed without
a reserve only when the source-ranked player damage budget covers the target HP
ceiling and expected incoming exchange. Preserve this boundary in candidate
selection and policy selection; do not let a fuzzy target bypass it through a
stale checkpoint.

Policy revision 195 keeps retryable liquidation ahead of the generic
source-ranked frontier, so fresh loot is sold before another funding hunt. Its
only transit-risk exception is the explicit Mage/Witch familiar probe: one
single transit-risk rejection may be admitted only when the outdoor, unarmed,
familiar damage-window contract passes. Any additional autonomy rejection, hard
route hazard, armed target, or special procedure still blocks the probe.

Policy revision 196 closes the post-loss plain-target escape unless the loaded
source world and live character state provide an audited player damage budget
covering the target HP ceiling and expected incoming exchange. A low source
incoming peak alone is not enough to authorize another unprotected probe after
a same-level XP loss; sanctuary-backed and ordinary source-safe routes remain
available.

Policy revision 197 adds the source-gated Smithy hurl path. The estimator and
live starter require a matching current wielded weapon VNUM with observed
`EGO_ITEM_CHAINED` evidence; learned `hurl` proficiency alone is never a
combat budget or command authorization. Because the current DD4 GMCP encoder
does not expose the chained ego bit, retain the bounded `identify`-text
fallback and preserve the marker through campaign checkpoints.

Policy revision 198 narrows the emergency no-sanctuary route exception. A
source-aggressive transit mobile may be treated as incidental noise only when
its parsed, fuzzed level is at least ten levels below the character and it has
no attack program or unsafe special; typed non-combat procedures such as
`spec_fido` are allowed. Near-band, programmed, unsafe-special, and missing or
malformed source cases remain fail-closed.

The `matrix-coverage` ledger separates target-level evidence from
creation-to-target proof. Target evidence must come from a recognized
campaign checkpoint (`segment_complete`, `target_reached`, or
`target_reconciled`) in the entry's own database campaign; a global character
snapshot is never substituted. Strict creation proof additionally requires a
recorded creation decision in one of that campaign's segment runs. Treat
`target-reached` as resumed/partial evidence and `creation-to-target` as the
stronger status; neither is HERO proof without the corresponding fresh run.

The unprotected HP-fuzz exception is a single empirical opportunity, not a
general fallback: it is closed after any current-reboot XP loss at the current
character level. A fresh candidate must then use sanctuary or wait for a new
reboot. When a fuzzy target reaches combat, the starter also compares its live
GMCP maximum HP with the audited source action budget and withdraws immediately
if the target cannot be defeated inside that budget. This preserves measured
live `consider` as the authority on the loaded level while preventing a
nominally useful but overlarge target from consuming more XP.
The no-sanctuary protection fallback has the same route-safety boundary: its
candidate must have no source-identified attack-program or unsafe-special
transit mobile. A source-aggressive transit mobile is admissible only when its
parsed level, including the source fuzz margin, is at least ten levels below the
character and it has no attack program or unsafe special; DD4's harmless
non-combat procedures such as `spec_fido` may then be treated as incidental
route noise. A mobile with no `spec_*` procedure is not otherwise harmless;
ordinary DD4 `fight.c` combat can still disarm or damage the player. Persist
the exact route VNUM metadata and fail closed when source metadata is missing or
malformed. A fallback that reaches a disallowed source-aggressive transit
mobile is failure evidence and is terminal for that reboot, not a reason to
retry.
No-recall recovery must resynchronize when a successful flee advances the
character beyond the fixed return cursor. Once a known Midgaard healer-route
waypoint is observed, clear the stale cursor and follow the direct route to
healer room 3054; never replay its next command against the new room.

When the requested source target is aggressive and its minimum fuzzed level is
below `character_level - 5`, record `target is aggressive` in
`autonomy_rejections` during candidate construction. This pre-entry gate must
run before capacity or other research pools; legacy capacity-only candidate
records must be checked by the same gate before reuse.

Source candidate construction also hard-rejects a mobile with DD4's
`AFF_NON_CORPOREAL` flag: `fight.c` refuses attacks against that form, so a
sellable drop cannot make it a funding target. Capacity-only research remains
research evidence, but after exact live isolation and a safe live `consider`,
its bounded target stop may execute a fight; this does not promote the reset
capacity to verified progression evidence. Funding startup repair treats the
durable latest attempt as authoritative for legacy checkpoints whose bounded
attempt list omitted an `absent` or `crowded` marker.

Latest reassessment anchor (2026-09-06): Dorrik, dwarf warrior, is
checkpointed at 38105, level 25, 380076 XP, safely full in healer room 3054
with flight active. Runs 12406 and 12411 recorded distinct 419-XP route losses;
run 12412 reached an isolated Solace Secretary, observed only 95 damage against
80 received on a 585-HP live instance, and lost 324 XP on bounded withdrawal:
the Fleshmonger senior-guard's level-15 `greet_prog` companion can initiate
`mpkill`, and the source-reachable Arachnos Guardian can interrupt transit.
All three exact policies are quarantined before ordinary selection. Policy
revision 196 now requires source-backed player-output and incoming-exchange
proof before another post-loss unprotected HP-fuzz probe. The ordinary Arachnos
candidate is now closed; only the separately bounded Mage/Witch familiar probe
may carry the single transit-risk exception. No level-26, subclass, or HERO
proof is implied.
12372-12375 exposed the sanctuary-loss boundary, a safe expired-reserve stop,
and 419- and 340-XP source-ranked losses without death. Run 12376 reacquired a
verified purple potion for 100 required-loot XP. Run 12377 consumed it before
killing Mr. Smithy for 1619 XP and returned safely at the bounded runtime
checkpoint. Run 12378 confirmed the Temple Square drunk hazard and deferred
flight purchase without entering the shop. Run 12379 reacquired the verified
purple reserve for 100 XP and returned safely. Run 12380 then recorded 117
partial combat XP and a 419-XP flee loss on the unprotected Secretary route;
GMCP established the authoritative net delta as -302 XP, and the policy is
quarantined. Run 12381 repaired the checkpoint and reacquired the purple
reserve for 100 XP. The next route can use that reserve or pass the ordinary
source-output and HP-window gates. Kestrel remains the level-24 thief
maintenance frontier at checkpoint 37990; Aeloria is level 18 and Praelarran
level 20. These are continuation and failure evidence, not subclass or HERO
proof.
Runs 12382-12389 then quarantined the Weeping Willow and Ki-Rin throughput
routes, reacquired sanctuary after a reset, and left Dorrik at 378806 XP. Run
12390 killed the Solace Secretary for 2032 XP and returned safely; run 12391
rejected crowded Mr. Smithy stables without combat. Runs 12392-12393 recorded
a bounded Windows socket failure and a finite return-home retry failure, with
no XP change. Connection-loss failures now persist an explicit return-home
marker and clear stale target/crowd observations before the next selection.
The offline suite passes 3647 tests.
Praelarran remains checkpoint 37939 at level 20 and Aeloria is now checkpoint
37994 at level 18; both are safely at the Healer. Run 12365 selected Aeloria's
source-ranked Arachnos guardian route, summoned and grouped the level-15 pony,
ordered it to engage, withdrew it near target finish, and reconciled a 633-XP
player kill before the controlled runtime cap. The complete suite passes 3618
tests. This is fresh continuation evidence, not level-19, level-25, subclass,
or HERO proof; the HP-fuzz, live-budget, and familiar repairs remain bounded
and must be repeated across later level bands.
Run 12327 died and exposed survival-priority, duplicated GMCP, and timeout
snapshot failures; run 12328 recovered the corpse. Run 12335 exposed a hard
Shadow Grove preflight hazard and two stale-snapshot flee losses totalling 464
XP. Runs 12336-12337 then returned safely: one clean research pass added 232
net XP without an objective kill, and the following hunt stopped before combat
because no executable sanctuary reserve was available. The accepted mage
training refresh is live-validated, including `burning hands: 31`. Run 12338
also showed that an unprotected source-ranked target must fit its audited HP
ceiling, not merely its nominal level or per-round damage bound; the 298-XP
net loss is retained and that route is quarantined. Run 12339 completed
sanctuary recovery safely with no XP change. The death and route losses remain
evidence. Run 12341 then calibrated the source-backed Secretary probe: two
burning-hands exchanges dealt 77 while Aeloria took 60, and the bounded
withdrawal lost 125 XP. The route is quarantined. The complete suite passes
3531 tests.

Current live frontier (2026-09-06): campaign 7, Dorrik, dwarf warrior,
checkpoint 38105, level 25, 380076 XP, healer room 3054. Revision 197 now
requires source-backed player-output and incoming-exchange proof before a
post-loss unprotected HP-fuzz probe; revision 194 still sanctuary-gates the
ordinary current-reboot recovery case. The Astra calibration additionally lets
the live damage-window probe
extend its conservative action horizon only when measured damage and the
current HP reserve support the projected exchange. Campaign reserve accounting
does not treat sanctuary duration 0 as durable outbound protection, although
the live starter still treats the affect as active until GMCP removes it. Run
12378 recorded the shop hazard and run 12379 reacquired a verified purple
reserve through Moria. The live observation layer also reconciles DD4's
multiline flee-loss and partial-combat-XP output with an already-authoritative
GMCP progress snapshot; runs 12380-12381 are the parser regression and repair
evidence. Runs 12392-12394 are bounded socket outage and live recovery
evidence, not progression. The offline suite passes 3647 tests. This is
continuation and safety evidence, not level-26, subclass, or HERO proof.
A read-only source-catalog audit found no fresh level-25 warrior target that
passes the revised player-output budget and route-hazard gates. The remaining
plain unprotected Secretary is the exact quarantined policy; wait for a new
reboot or a verified sanctuary reserve before the next live combat attempt.

Historical Praelarran anchor (2026-09-05): campaign 30, Praelarran, human warrior,
checkpoint 37939, level 20, 224053 XP, healer room 3054. Run 12342 completed
a bounded sanctuary-recovery check without XP change; the next bounded resume
confirmed the same current-reboot cooldown and awaits the field-area reset. The
offline suite passes 3531 tests, including shared combat priority, death recovery, fresh
timeout snapshots, mage training, and static-audit labeling. Run 12282 exposed the
Sentinel Gap tree-sprite
route's rock-crab `spec_breath_gas` hazard after an incidental 110-XP Toede
kill; the bounded return cost 270 XP, net -160, and that policy is quarantined.
Run 12283 then retried sanctuary recovery after one bounded reset wait, found
source mobile 4056 blocking the Moria required-loot endpoint, and returned
safely without a potion or progression claim. Run 12284 selected the newly
unblocked Eastern Desert worm route, completed one objective kill for 585 XP,
and returned safely to healer room 3054 without death, flee, or XP loss. Run
12285 then completed a bounded provision-funding sweep that recorded the Midget
as absent without claiming XP. Run 12286 moved to Katrina the Shepherd, added
60 XP, and returned safely to the healer. Run 12287 then liquidated the
resulting loot and returned safely with XP unchanged. Run 12288 completed a
source-backed patrolling-guard funding kill for 100 XP, run 12289 liquidated
safely, and run 12290 killed the source-ranked Dwarven giant for 499 XP with a
full healer return. Runs 12291 and 12292 then killed a Dwarven thief for 982 XP
and a Dwarven giant for 535 XP, both with safe healer returns. Run 12293 then
recorded a 320-XP Dwarven Home withdrawal and quarantined that policy; runs
12294 and 12295 recovered 472 and 558 XP from fresh Dwarven giant kills. Run
12296 added 539 objective XP and 30 incidental XP before a safe return; run
12297 completed without an objective kill, and run 12298 completed sanctuary
recovery with 100 XP. Run 12299 quarantined the Goblin Caves Sentry after DD4
reported a 270-XP flee loss and 69 partial combat XP. Its GMCP worth packet
recorded the authoritative net result of 219584 XP; the old segment snapshot
at 219314 had applied the full loss twice. The parser now retains partial XP
evidence and the full suite covers the repair. Run 12300 found the Moria
sanctuary endpoint absent and returned safely without a potion or objective
XP. Runs 12301-12305 continued safe funding and maintenance, adding 100, 60,
and 90 XP from source-ranked guard targets; the intervening sale route remained
bounded by the shared shop hazard. Runs 12307-12308 then killed Dwarven giants
for 495 and 472 XP. Runs 12309-12311 completed liquidation, flight maintenance,
and another safe sanctuary check; run 12312 rejected the crowded White Stag
route without XP. Runs 12313-12314 then added 693 XP from the Arachnos guardian
and 609 XP from the Eastern Desert worm, and run 12316 added another 580 XP
from the guardian. Run 12317 rechecked Moria safely but still found the source
orc blocking the sanctuary endpoint. Runs 12318 and 12320 added 110 and 529 XP
from fresh source-ranked targets; runs 12319 and 12325 deferred liquidation at
the shared Temple Square shop hazard, and run 12321 added 100 XP from funding.
Runs 12322 and 12324 completed safe maintenance, while run 12323 added 531 XP
from a Dwarven giant. Run 12326 found no safe current-reboot funding target for
the patrolling guard and checkpointed without claiming progression. Praelarran
is now checkpointed at 37891 with 224053 XP. Protection recovery remains
governed by the existing live gates; no level-21, subclass, or HERO proof is
implied.
Runs 12266-12271 confirmed the shared Temple Square shop boundary, recorded
the Midget as absent, added 50, 70, 60, and 40 XP from fresh funding targets,
and acquired useful gear including the yellow-and-green ring and Katrina's
sword. Persist latest sale amounts separately from cumulative proceeds, prefer
source-known coin carriers when flight funding is short, and age a temporary
city-shop cooldown after productive funding kills. Runs 12185-12189 recovered a
purple sanctuary potion, restocked, tested an independent Mirror Realm
watchman, and rearmed the warrior's dagger. Run 12190 exposed a real Moria
recovery hazard: the deep required-loot search crossed source-reachable
aggressive Warrior and Mage mobiles and lost 768 XP before a safe healer
return. Runs 12191 and 12193 then confirmed Secretary and Dwarven giant kills
for 910 and 568 XP, while 12192 completed a safe Shire rotation. Run 12194
bought flight at the observed reboot-local price; run 12195 killed the Eastern
Desert worm for 841 objective XP but lost 256 XP to a drider during the
no-recall return; run 12196 liquidated the loot and returned safely. Run 12197
reached the Solace administration corridor three rooms short of its endpoint
at a bounded 120-second cap without making a progression claim. Run 12198
killed the Eastern Desert worm for 767 objective XP and live-validated the
recovery repair: after exiting to room 5007 it recalled without a pursuer, flee,
XP loss, or death. Run 12202 repeated the repaired worm route, adding 20
incidental XP and 875 objective XP with another safe no-recall return. No
level-20, subclass, or HERO proof is implied. Run 12204 added 90 incidental XP
from a drider, rejected the unsuitable nomad leader after live `consider`, and
returned safely through the repaired no-recall route. Run 12205 sold the drider
dagger at the weapon shop; run 12206 bought and quaffed the reboot-local
light-blue flight potion for 131 copper and returned to the healer. Flight is
active for the next field segment. Run 12207 killed The guardian in Arachnos
for 1091 objective XP and returned safely through the repaired no-recall route.
Run 12210 retried the worm, earned 426 partial XP, withdrew at 75/440 HP, and
paid a 256-XP flee loss before returning safely. Preserve this route-loss
evidence and rotate away from the exhausted worm policy. Run 12211 then killed
The guardian for 715 objective XP and returned safely through the repaired
no-recall route, leaving 96 XP to level 20. Run 12212 crossed level 20 with a
665-XP Secretary kill; DD4 awarded 24 hitpoints, 7 mana, 10 movement, 2
physical practices, and 1 intellectual practice. Level-20 trainer and subclass
evidence is now the next live gate; no subclass or HERO proof is implied. Run
12213 trained strength at the Kerofk Captain, raised enhanced damage to 61% and
unarmed combat knowledge to 59%, and returned with 587 objective XP plus 480
incidental XP from below-band transit mobs. Run 12214 killed the Old Treant for
1167 objective XP, dropped and sacrificed its arm, sacrificed the corpse, and
returned safely through the repaired no-recall route. Run 12215 restored the
light-blue flight reserve, run 12216 completed a bounded Mirror Realm probe
without XP, and run 12217 killed two live Secretaries for 1841 objective XP
before returning safely. Run 12220 killed another Old Treant for 1198 objective
XP and returned safely through the repaired no-recall route. Runs 12221 and
12222 completed bounded Mirror Realm and Solace no-kill rotations without
unsafe combat. Run 12223 killed the level-20 giant purple sand worm for 534
objective XP, recovered a pink potion, exited the no-recall room, and recalled
safely without flee, death, or XP loss. Run 12224 completed bounded flight
maintenance with no XP change and left the character safely checkpointed for
the next target selection. Run 12225 reached the Mahn-Tor Old Treant route but
encountered an unexpected dark ethereal knight at the bloody intersection. The
bot withdrew at 75/464 HP, received 293 partial XP, paid a 270-XP flee loss,
and returned safely; the resulting net gain was 23 XP. Treat that route as
concrete hazard evidence, not an objective kill. The next executable work is
continued level-20 progression toward level 21, followed by fresh trainer and
subclass validation; no level-21 or HERO proof is implied. Run 12226 completed
the bounded Moria sanctuary-recovery segment with no XP change and left a safe
healer checkpoint for the next independent target. Run 12227 killed an
incidental city drunk for 10 XP and the level-20 giant purple sand worm for 630
objective XP, recovered a pink potion, and returned safely through the no-recall
boundary without XP loss or death. Run 12228 completed safely but found the
Shadow Keep Undead Soldier route crowded, including a multi-mobile underwater
room, so it did not execute the exact isolated target stop or claim XP. Run
12229 safely rejected the Crystal White Stag route after reaching an Ambush
clearing with a wounded goblin and the Forest foothills without finding an
isolated target; it claimed no XP. Run 12230 then killed the giant purple sand
worm for 589 objective XP and returned safely through the no-recall boundary
without flee, death, or XP loss. Its potion, wand, and bow drops hit the
carrying limit, so the next maintenance pass must liquidate or discard loot
safely. Run 12231 completed a bounded Mirror Realm young-boy attempt safely
without converting the research target into an isolated kill or claiming XP.
Run 12232 killed the giant purple sand worm for 778 objective XP, then reached
the runtime boundary while checking the healer checkpoint; the kill was
reconciled, but the segment failed after connection-inactivity retries. The
safe-healer cleanup predicate now trusts the live room and enemy state even
when the policy combat flag is stale, covered by the full offline suite. Run
12233 then recovered the character to healer room 3054 at full health but hit a
separate silent equipment-audit acknowledgement boundary; it changed no XP and
remains a startup-recovery failure, not a progression claim. Runs 12234-12235
completed bounded flight-purchase and healer-recovery attempts; run 12235
confirmed live `where drunk` hazards at Main Street and Eastern End of Poor
Alley, so the shared shop route remains blocked. Run 12236 safely completed the
Mirror Realm watchman research probe, and run 12237 restocked provisions. Run
12238 killed a source-verified dwarven thief for 1043 objective XP; run 12239's
Moria sanctuary-recovery route recorded 90 XP from a large hobgoblin while
restoring resources. Run 12240 encountered the Shadow Keep watchman with
sanctuary active, was disarmed, recovered its sword, and withdrew at 22% health
after a bounded fight, losing 128 XP; quarantine that policy. Run 12241 safely
probed the Shadow Keep undead-soldier route, and run 12242 completed Moria
sanctuary recovery with 100 XP, ending at full health and movement in healer
room 3054. Runs 12243-12245 then completed a bounded Moria recovery, selected
the source-ranked Goblin Caves Sentry, and withdrew after sanctuary expired at
34% health following two live disarms; the route lost 270 XP but dealt 287
partial damage XP and is now quarantined. The follow-up rearm bought and
wielded a source-backed dagger and saved in healer room 3054. The current
checkpoint is safe at level 20; no level-21 or HERO progression is claimed.
Runs 12246-12248 then completed a bounded Thain rotation, exposed a funding
route that attacked an armed Mirror Realm young man and lost 270 XP while
earning 214 partial XP, and safely skipped the below-band Circus Midget. The
source audit confirmed that Mirror Realm mobile 19005 carries a knife and
3,280 copper. Funding selection must honor the ordinary armed-target sanctuary
gate; the regression is covered by the full suite. The next live funding
candidate is the lower-peak Miden-nir guard, and remains maintenance rather
than progression evidence.

Historical live anchor (superseded 2026-09-04): campaign 30, Praelarran, human warrior,
  checkpoint 36642, level 18, 159206 XP, healer room 3054, with 18444 XP to
  level 19 and a long sword wielded. Flight is not active; the observed price
  is 104 copper and the current carried balance is 85 copper-value. The latest
  checkpoint is fully recovered. Runs 11982-11984 added 170 incidental XP and
  1030 objective XP before the runtime-cap checkpoint; run 11985 restored the
  primary weapon with 30 incidental XP. Run 11986 reselected the Arachnos
  route, but withdrew at 50/416 HP after a source-known drunk interruption,
  adding 51 net XP and no objective kill; this did not validate the
  cap-after-kill repair. The intervening liquidation completed safely, and run
  11988 killed the lemming smithy (mobile 29953) for 672 objective XP. Runs
  11989-11991 then added a 628-XP Secretary objective kill, clean Moria
  recovery, and a 765-XP repeat Lemmings Smithy objective kill. The protection
  hold remains attached to the failed Lord Doom policy, and a fresh live run
  that both kills and reaches the controlled cap is still required.
  Runs 11992-11994 then recorded a blocked liquidation boundary, a Secretary
  runtime-cap return without a kill, and a live below-band Lemmings result;
  all three returned safely without new XP loss. The next level-18 rotation
  must select an independent source-ranked candidate.
  Runs 11995-11997 then repeated the known liquidation boundary, completed
  flight maintenance, and returned through liquidation without XP change or
  loss. The next invocation must obtain a fresh field decision rather than
  repeat maintenance indefinitely. Run 11998 then selected Queen Spider and
  recorded a live crowded stop without XP change or loss; the next candidate
  must be independent of that crowd result.
  Run 11999 completed restock safely; hunger 39, thirst 47, movement 319,
  weapon state, and empty wear-slot checks were healthy. The next field
  decision can proceed without a provision or equipment maintenance blocker.
  Run 12000 selected Essabella but intercepted the target below the 95%
  field-health gate; a below-band goblin guard added 110 incidental XP. The
  sanctuary recovery gate remained on its current-reboot cooldown, so
  checkpoint 36553 stopped safely and the next attempt used the bounded reset
  wait. Run 12001 then exposed a live Moria pre-entry gap: `scan down` named
  source mobile 4056, an aggressive orc one room below room 4064, but the old
  allow-list did not classify it before entry. The first recall failed and the
  second recall cost 232 XP; Praelarran remained alive and returned to the
  Healer at checkpoint 36556. The source-aware scan repair is offline-verified
  and awaits fresh live validation; this is a safety reproduction, not
  progression proof. Runs 12002-12004 then completed clean Dwarven giant and
  Queen Spider checks followed by the expected protection-recovery unavailable
  checkpoint, all without XP change, death, or additional loss. The next
  invocation uses the configured automatic reset wait for fresh sanctuary
  evidence.
  Run 11975 completed the Shadow Keep circuit without XP change. Run 11976
  completed the Solace Lord Doom research probe without XP change. Run 11977
  tested the corresponding hunt: Lord Doom disarmed the warrior and the bot
  withdrew at 60/416 HP after partial damage, recording the 34-XP loss and
  quarantining the policy. Run 11978 safely recovered through Moria and killed
  the below-band orc for 100 incidental XP. This is fresh level-18 safety and
  recovery evidence, not subclass or HERO proof.
  Runs 11979-11981 then completed a clean rotation: Wyvern returned with no XP
  change, Dwarven Home added 80 XP, and flight maintenance completed without a
  loss. Run 11985 rearmed the primary weapon and left all wear slots populated.
  Run 11958 live-validated a source-ranked Bird Spider objective kill (mobile
  6310, room 6342) for 369 XP and returned safely at the segment boundary
  without adding an XP loss.
  Runs 11959-11961 live-validated that a recoverable city-shop route hazard
  now advances a two-segment invocation to an independent Dwarven giant
  route and then the sanctuary-reserve pass; both later segments returned
  safely, with no XP change. This is continuation evidence only, not
  subclass or HERO proof.
  Runs 11934 and 11936 added 277 and 554 XP from the same independent policy;
  run 11935 completed the repaired Dwarven route without XP change or loss.
  Run 11937 live-validated the Moria pre-entry scan: `scan down` ran from room
  4020 before room 4064, found no warrior 4051, and the route acquired the
  purple potion after two bounded endpoint kills. The specific hazard-blocking
  branch remains research-gated until that warrior appears in a live scan.
  Run 11938 added 80 XP from Shadow Keep, run 11939 completed a clean
  sanctuary-reserve probe without XP, and run 11940 exposed a 73-XP Shire
  Thain combat-throughput loss after sanctuary expired with the target at 80
  percent; that source policy is now quarantined. Runs 11941-11942 completed
  flight and Moria maintenance without XP, run 11943's protected Wyvern retry
  added 494 XP, and runs 11945-11946 added 70 XP through source-backed
  funding. The character remains alive and fully recovered; preserve the loss
  history instead of treating it as progression.
  Run 11932 exposed the remaining Moria timing bug: two source-registered
  warriors entered room 4064 before the endpoint hazard gate and cost 208 XP.
  The repair now scans the immediate destination before final entry; focused
  and full offline tests pass.
  Runs 11924-11925 validated the
  repaired frontier rotation: a crowded Queen Spider route withdrew without
  an objective kill, then the Bird Spider route completed an objective kill
  for 566 XP. Run 11926 refreshed flight at the observed 104-copper price.
  Run 11927 correctly recorded that no independent source-safe target remained
  while protection recovery was pending. Run 11928 rechecked the exact Moria
  sanctuary carrier after the bounded reset wait; it was absent, so the
  character returned to the Healer without claiming a purple potion or
  progression proof. The protection marker remains active and the campaign is
  ready for the next fresh source or reboot boundary. Runs 11737-11743
  completed the level-
16 Mahn-Tor handoff, maintenance, and Bardoosh frontier, reaching level 17
without death or XP loss. Runs 11744-11749 added 1152 XP from Bird Spider,
Bardoosh, Wyvern ranger, and Mahn-Tor routes. Runs 11750-11752 added 370 XP
from the Wyvern ranger; liquidation completed once and then deferred after
three bounded checks found the source-backed Midgaard drunk hazard. Run 11753
exposed a delayed wield-result bug in rearm; run 11754 live-validated the
repair. Runs 11755-11757 added 1071 XP from Bardoosh and Bird Spider, with
flight maintenance and healer returns. Runs 11758-11760 added 820 XP from
Mahn-Tor and Bardoosh, with clean liquidation. Runs 11761-11763 added 880 XP
from Bird Spider and Bardoosh, with clean liquidation. Runs 11764-11766 added
876 XP from Mahn-Tor and Bardoosh, with clean liquidation. Runs 11767-11769
  added 900 XP from Bird Spider and Bardoosh, with clean flight maintenance and
  healer returns. Run 11776 recorded an unexpected combat interruption on the
  Shadow Grove no-combat probe, costing 1040 XP without death; startup repair
  now reconstructs and preserves that current-reboot route quarantine from
  segment history. Run 11779 selected independent Bardoosh combat and added
  531 XP, returning safely to the healer. Run 11780 selected the independent
  Wyvern ranger route and added 336 XP; run 11781 deferred liquidation after
  three bounded checks found the same source-backed drunk hazard. Run 11790
  live-validated duplicate-armour capacity relief, pie restock, and healer
  return; run 11792 completed liquidation, and run 11793 added 589 XP from
  Bardoosh without loss. The selector is now executing level-17 frontier
  candidates rather than replaying stale research. The full offline suite
  passes 3348 tests. Runs 11799-11801 added 411 XP from the Shadow Keep probe
  and Bardoosh, with clean liquidation. Runs 11802-11804 added 438 XP from
  Bird Spider and 328 XP from the Wyvern ranger; two intervening repeat checks
  returned safely without XP. Runs 11805-11808 added 904 XP from two Wyvern
  ranger kills and the Shadow Keep circuit, with clean liquidation and healer
  returns. Runs 11809-11814 added 298 XP from the Wyvern ranger; the Dwarven
  Home check returned safely without XP. Runs 11815-11816 safely exposed the
  full-capacity edge at the Bakery; run 11817 then dropped and sacrificed the
  source-matched long bow that a warrior cannot use, bought a pie, and returned
  to the healer. The 30 XP change was incidental drunk-crossing XP, not
  progression credit. Run 11818 completed a clean Dwarven giant check; run
  11819 added 501 XP from the Wyvern ranger. Run 11820 exposed an unsafe
  level-17 deep Moria transit after the carrier was absent, recorded 624 XP of
  bounded flee/recall loss without death, and returned safely to the healer.
  The source graph now gates that deep route and limits lower-level recovery to
  the safe reset room. Runs 11821-11823 completed restock, added 440 XP from
  the Wyvern ranger, and bought flight without entering the quarantined Moria
  route. Runs 11824-11828 then added 494 XP from Bird Spider and 80 XP from
  the Eastern Desert nomad commander; a partial Wyvern exchange in run 11825
  cost 208 XP, run 11826 rearmed the dagger, and run 11827 returned safely
  without XP. The five-segment pass produced a net 497 XP from the prior
  anchor. The full offline suite passes 3359 tests. Run 11844 live-validated
  reconnect recovery from the final Mud School corpse: the bot dropped a
  duplicate carried bracer, recovered the iron key, unlocked and opened the
  northern exit, reached healer room 3054, slept, saved, and quit. This is
  continuation evidence only; it does not prove subclass selection or HERO.

Runs 11847-11848 live-validated exact object-selector food recovery and added
180 XP. Runs 11849-11851 completed liquidation, restocking, and flight
maintenance safely. Runs 11852-11857 completed sanctuary recovery, Shadow
Keep, Bird Spider, and Queen Spider rotations, adding 1323 XP without death;
the character ended back at healer room 3054. These are current-band
continuation results only; they do not prove level 18, subclass selection, or
HERO.

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
area-reset window, completed Moria sanctuary and Shadow Keep checks without XP,
then reopened the source-ranked Midget funding route and added 30 XP. The
latest durable checkpoint is 36124 at 149380 XP; the purse is 2 gold, 2 silver,
and 118 copper, and the blocked-shop flight cooldown has aged to two steps.
This remains continuation evidence, not level-18, subclass, or HERO proof.

The next ordinary rotation inspected the source money container without XP,
then completed two source-ranked Midget funding kills for another 30 XP. The
latest checkpoint is 36132 at 149410 XP, with 172 copper plus 2 gold and 2
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
is 36160 at 149430 XP; the observed flight price is 104 copper and the route
cooldown has reset to three steps. This is continuation and route-safety
evidence, not flight acquisition or level-18/HERO proof.
The following bounded rotation completed safely at checkpoint 36174. Moria
and funding maintenance added no XP, while the Shadow Keep route recorded a
30-XP incidental kill of the source-scripted drunk before returning to the
Healer; it did not count as an objective kill. Source analysis now records
that program as route risk, hard-rejects deterministic program attackers, and
keeps probabilistic wandering hazards visible without suppressing the entire
level frontier. This is continuation evidence only, not level-18 or HERO
proof. The full offline suite passes 3362 tests.

The final tutorial controller disables autoloot before the gladiator fight and
selectively retrieves only the source-required bracers, stone, and iron key.
When a reconnect finds the gladiator corpse but no live target, it resumes the
loot-and-exit sequence. Carried capacity relief uses `drop`, because DD4's
`sacrifice` command searches room contents rather than inventory; exact target
selectors are retained when the live inventory exposes them.

Historical live anchor (superseded 2026-09-03): campaign 30, Praelarran,
checkpoint 35469, level 16, 129970 XP, healer room 3054. Runs 11589-11597
added 1888 XP through source-ranked funding and field routes, including a
reboot-priced flight purchase at 104 copper. Run 11607 recorded a 38-XP
no-recall recovery loss without death; run 11608 returned cleanly through
liquidation, and run 11610 earned 300 XP from the same Eastern Desert route.
Runs 11611-11616 continued bounded source-ranked rotation with productive
Bird Spider and caretaker results plus safe maintenance. Run 11617 found the
drow guard route unsafe, cost 188 XP without death, and was quarantined. Run
11618 selected an independent quasit route and completed safely without XP
change. Run 11619 retried sanctuary recovery after the bounded reset wait,
found the exact carrier absent, and recorded 70 incidental XP from one
below-band warrior without loss or death. Run 11620 killed the source-ranked
Wyvern ranger for 411 XP and returned safely. Runs 11621-11623 completed
liquidation, rearm, and flight maintenance; run 11624 killed Bardoosh for 564
XP and returned safely. Run 11625 completed liquidation, and run 11626 killed
the Wyvern ranger for 351 XP with a safe healer return. Run 11627 completed
liquidation, and run 11628 retried sanctuary recovery, found the exact carrier
absent again, and returned safely without XP change. Run 11629 repeated Bardoosh
and earned 497 XP before the bounded field cap, then returned safely. Run 11630
completed liquidation; run 11631 killed the source-ranked Wyvern ranger for
548 XP and returned safely after a live disarm left the primary dagger
unrecovered. The starter now withdraws from combat when its dropped weapon
cannot be recovered, leaving the next campaign segment to perform verified
rearm maintenance. Runs 11632-11635 completed compatibility liquidation,
dagger rearm, flight funding, and a 624-XP Bardoosh kill. Run 11636 added 287
XP from a Wyvern ranger but stopped at the Mud School supply room after its
loot exhausted pie capacity; run 11637 returned safely to the healer, and run
11638 added 433 XP from Bardoosh. Run 11639 exercised bounded provision
funding, run 11640 restocked a big pot pie at the Bakery, and run 11641
confirmed the Moria sanctuary carrier absent before a safe healer return. Run
11642 killed the Wyvern ranger for 488 XP. Run 11644 tested Bardoosh but lost
230 XP at the bounded runtime before a kill; both `get dagger` attempts were
confirmed by `You get a dagger` and `You wield a dagger`, so the route failure
was throughput and timing, not weapon recovery. Run 11645 killed the Wyvern
ranger for 596 XP, and runs 11646-11648 completed restock, a safe zero-XP
Shargugh evaluation, and a 345-XP Wyvern ranger kill. Runs 11649-11654 then
completed the bounded Moria sanctuary check, liquidation, Shadow Keep Wraith
evaluation, two safe zero-XP Shargugh evaluations, and two Wyvern ranger kills
worth 457 and 369 XP. Runs 11655-11665 continued bounded maintenance and
source-ranked rotation; run 11666 acquired the source-verified Moria purple
sanctuary potion, and run 11667 completed the Mahn-Tor warrior circuit for 315
XP with a safe healer return. Runs 11668-11671 rotated through an absent Haon
Dor endpoint, a second Mahn-Tor kill worth 381 XP, and two absent Shadow Keep
endpoints; run 11672 added 512 XP from a Wyvern ranger with a safe healer
return. Runs 11673-11675 completed rearm maintenance, a 375-XP Wyvern ranger
kill, and liquidation. Runs 11676-11678 completed rearm, a fresh Shargugh
absence, and a 370-XP Wyvern ranger kill. Run 11679 exposed a full item-slot
rearm failure; run 11680 then donated the redundant long bow and restored the
source-backed dagger after the capacity gate was fixed. Run 11681 recorded a
bounded 188-XP CrystalMire route loss and quarantine; run 11682 completed the
Shadow Keep research probe, and run 11683 killed an undead soldier for 765 XP.
Runs 11684-11686 completed another Shadow Keep evaluation, a 419-XP Wyvern
ranger kill, and liquidation. Runs 11687-11689 completed a Shargugh absence,
flight maintenance, and a 453-XP Wyvern ranger kill. Runs 11690-11692
completed a 70-XP Shadow Keep contact, a zero-XP Wyvern pass, and a zero-XP
Shadow Keep pass. Runs 11693-11695 completed a 60-XP Shargugh contact,
liquidation, and flight-potion maintenance.
The old level-15 protection marker remains audit history but no longer blocks
the level-16 frontier. This is continuation evidence only; it does not prove
subclass selection or HERO.

Direct fame-recovery stops that carry a protected source incoming bound and
still return a durability warning require a character-specific live damage
window probe before spending another combat reserve. Allow at most three
positive target-HP samples or 12 seconds, require at least 10% of the target's
observed maximum HP in damage, and withdraw before emergency potion handling
when that threshold is not met. Record the bounded no-kill result as research;
do not promote it to progression evidence or replay it blindly.

For ordinary source-ranked targets whose source HP ceiling exceeds the current
character maximum HP, the same probe uses a 25% observed-target-damage floor.
This stricter threshold prevents an initially favorable three-sample exchange
from approving a target that will outlast the character's full combat window.
When a current-reboot XP-loss route has one sanctuary reserve, record the
one-shot protected retry at selection time. A route-only crowd or hazard result
consumes that retry allowance even when no potion was spent; rotate to an
independent policy rather than reopening the same failed route.

Clean, unarmed, one-capacity fame targets may run without sanctuary only when
both source raw peak-round and critical-hit bounds are strictly below current
maximum HP. Keep exact targeting, isolation, live consider, route, movement,
and the bounded damage-window probe; any special, armed target, route hazard,
or other autonomy rejection remains excluded. A candidate rejected only for
source peak damage still requires sanctuary and its protected bounds.

The source-ranked selector must not dispatch an ordinary candidate whose
audited HP ceiling or combat path requires sanctuary when no executable reserve
is present. Otherwise the runner can spend a full bounded segment travelling
to a target that the field executor must reject before combat. Preserve the
separate admissions for explicit bounded-peak retries, sanctuary-resource
specials, and audited protection fallbacks.

For a Mage or Witch source-ranked stop, `require_familiar` is executable only
when live practice observed `summon familiar`, the source target is plain and
unarmed, every source-reachable target room is outdoors and non-underwater, and
the combined player-plus-pony damage budget fits the source HP ceiling and mana
reserve. The starter must summon, group, and order the pony before the opener;
it withdraws the pony near 45% target health so DD4 awards XP to the player,
and flees if the familiar is lost early. Treat the first live kill as bounded
continuation evidence, not general class or HERO proof.

When a source-ranked route exceeds the current movement pool, split it only at
source-audited `no_mob` rooms. Recover before issuing each long route leg, keep
the target suffix exact, and retain the complete outbound command path for a
bounded return if recall fails. Closed-door commands must reverse to
`open <opposite direction>` on return; randomized rooms and unverified
waypoints remain unavailable.

The damage-window probe starts before the opening attack. If no exact enemy HP
snapshot existed before that opener, the first exact single-target
`Char.Enemies` snapshot may use its live `maxhp` as the initial baseline so
opening backstab or opener damage is counted. This inference is limited to an
isolated target; never infer a full-health baseline from a multiple-enemy
snapshot. Keep the three-sample/12-second and 10-percent gates authoritative,
and treat a resulting low-damage failure as research rather than a parser
failure.

DD4's `fight.c` allows ordinary visible NPCs, not only `ACT_AGGRESSIVE` mobs,
to join a PC-versus-mobile fight. Different prototypes have a 1-in-8 join
chance and the same prototype always joins, within the source level window;
`update.c` can also let aggressive mobiles initiate independently. Never treat
non-aggressive or no-special status alone as a trivial companion. Only source
non-interaction, the explicit below-band rule, or a proven level-window
exclusion may remove a bystander from the combat hazard set.

Quest progression is now an explicit observed gate. DD4 `Char.Quest` snapshots
are deduplicated, persisted in campaign state, rendered in reports, and feed
bounded request, target, and completion policies when
`level_qp_shortfall > 0`; required healer, funding, and recovery maintenance
still takes precedence. Suturb is source-registered through level 25, and the
checked-in source graph now provides the explicit Goldmoon route to room 10024
for levels 26-100. `server/src/update.c` gates advancement at current levels
29, 49, 79, and 99, meaning the next levels are 30, 50, 80, and HERO 100;
the quest helper reconstructs those requirements when an older checkpoint has
total points but no live requirement fields. Live checkpoint 26804 preserved
Corararfen's available status, zero points, and zero shortfall after a clean
continuation. Exact object/hoard retrieval and the remote Ota'ar Dar
questmaster boundary remain research-gated, so no level-30, subclass, or HERO
proof is implied. The source audit now mirrors DD4's ITEM_DIGGER, form, and
digging-weapon checks; an active hoard quest without a capability selects the
bounded `quest-digging-tool` policy, which acquires exact shovel VNUM 3604 from
the source-reset Graveyard shed at room 3613 before target dispatch. Dynamic
quest preflight now records a ready/unavailable checkpoint without Telnet
action when the source mirror or exact VNUM is unavailable. When the source
graph proves that an active quest room is inaccessible from Midgaard, the
runner follows DD4 FAQ 5.4 and uses the registered questmaster route to issue
`QUEST ABORT`, then waits for the server's cooldown before requesting a
replacement. This is distinct from source absence and is covered by live run
9043 against retrieve quest room 285.

The checked-in `matrices/level-10-all-race-class.yaml` declares every current
source-legal race/base-class pair (225 at the 2026-08-17 catalog revision) for
the level-10 validation phase. A declared entry is not live proof until its
campaign checkpoint reaches level 10; keep the smaller `matrices/level-10.yaml`
for the quick three-character rotation.

The fixed registry has an intentional level-11 handoff for tutorial-arena
classes: after their level-10 scout, `policy_for` returns the research-status
generic source-ranked frontier at the first uncovered level. From level 10
onward the campaign runner may also put an executable generic candidate ahead
of an ordinary fresh named probe; if no safe candidate exists, that probe is
retained as fallback. Dedicated resource, class/shared evidence, and all
mandatory transition policies remain authoritative. At level 81 and above the
same generic frontier keeps the HERO path executable while late-band routes
are researched. This is a research handoff, not verified progression evidence;
retain all live source, route, consider, health, resource, and healer-return
gates.

Negative fame recovery may use the generic source-ranked selector only for a
fame-eligible ordinary mobile whose source level range intersects
character-level +6 through +9, with sanctuary-protected damage below current
maximum HP and an exact isolated endpoint. If that fame frontier is empty, do
not fall back to an ordinary below-band hunt; persist an explicit unavailable
or reset-wait result and preserve the negative-fame gate. A live room hazard,
including a special-capable bystander, is authoritative crowded research and
must rotate the candidate rather than start combat.

The fixed registry also contains the research-status
`mahntor-rock-toad-warrior-circuit-16-18` continuation. It is available only
to warriors at levels 16-18 after positive class-tagged Mahn-Tor level-13-to-15
evidence, and it uses the existing circuit executor with source mobile 2303,
the conservative 140-damage peak bound, exact live `consider`, crowd, health,
movement, encumbrance, and healer-return gates. Run 10906 supplied warrior
evidence at level 15; it does not prove the new level-16 band, and the policy
must remain `research` until a fresh level-16 warrior result is recorded.

The same registry now carries
`mahntor-rock-toad-warrior-circuit-19-20` as a separate research-status
continuation. It is available only to warriors at levels 19-20 after a positive
result from the level-16-to-18 policy; it inherits the same source mobile,
140-damage peak bound, live `consider`, crowd, health, movement, encumbrance,
and healer-return gates. This is a policy handoff, not level-19 or level-20
progression proof; each band still requires a fresh live result.

The level-30 subclass combat boundary now consumes live-known capabilities for
safe single-target actions and self-protection: druid `bark skin`, monk
`mental barrier`/`displacement`, barbarian `berserk`, vampire `suck`, and
martial-artist `atemi`/`kansetsu`, and thug `smash`. Berserk is one-use per
target; targeted actions use the existing between-round cooldown. Area-wide
spells, forms,
songs, turrets, runes, and other lifecycle-sensitive abilities remain
research-gated until their target, resource, and expiry policies exist.

The level-30 subclass handoff is source-capability-gated. Parse mobile teaching
entries from the read-only area files and require `teacher base`, the exact
`<subclass> base` entry, a source reset, and a source route from recall before
selecting a subclass. Engineer and runesmith use Anon mobile 31002 (Jolob in
room 31041); Kerofk's Gorn does not teach either one. The resolver is reusable
source/preflight evidence, not live level-30 transition proof.

The early tutorial fallback opens at level 6 only after the Mud School and
Dragon Cult routes have produced same-reboot exhausted or unavailable evidence.
It uses the distinct `source-ranked-hunt-6-10` policy identity and may select a
source-ranked target from the broader low-level catalog, but must retain the
same exact source identity, live consider, crowd, route, health, resource, and
healer-return gates. Runs 8295, 8301, and 8302 live-validated class-tagged
Praelarran kills; run 8296 rotated to an absent Cult fanatic without replaying
the first target. This is executable early-band evidence, not level-10 or HERO
proof.

The source-ranked selector normally stops when the current reboot has no
fresh, safe candidate. After its ordinary safe pools are exhausted, both a
normal resumable invocation and an explicit `retry_stalled` request (CLI
`--retry-stalled`) may reopen one fresh candidate blocked only by trailing
no-progress history. This fallback must not override live absence, crowd,
route, consider, protection, resource, source-identity, or cooldown evidence.
Record the bounded retry and rotate after its live result instead of replaying
a blocked policy indefinitely.

If a source-ranked route is interrupted by an allowed harmless below-band
transit fight before its endpoint, completion must resume the remaining
official outbound commands before invoking destination-guided hunt planning.
The hunt planner only has endpoint stop routes and cannot reconstruct an
unfinished official route from the interruption room.

When a current-reboot source policy's latest bounded result is incomplete and
its latest objective delta is negative, block it from ordinary retry even if
the boot kill count is below three. An explicit XP-loss record remains under
the protection-recovery contract: the normal retry requires a sanctuary
reserve, and a second loss quarantines the route. If the source-verified
sanctuary route is current-reboot absent, cooling, or terminally exhausted and
no reserve is available, one distinct `protection-recovery-ordinary` fallback
may reopen
only a fresh or already-productive, source-safe, special-free, no-flight target
in the useful band. Reuse of an already-productive target requires an exact
current-reboot positive live result, fewer than three boot kills, and source
peak damage at or below 80% of maximum HP, with the source lower HP bound no
higher than the character's maximum HP. It starts at 95% health, is recorded
before execution, and is quarantined after another failure; a positive
objective kill clears the protection hold. Count an explicit increase in the durable `xp_loss_total`
counter as a loss even when partial combat XP makes the segment's net XP
positive. Startup repair and live segment finalization must use that event
evidence so a route cannot evade second-loss quarantine through partial XP.
This does not bypass absence, crowd, route, consider,
resource, source-identity, or cooldown evidence.

The ordinary fallback target does not need its own earlier loss record: the
current protection hold's exact one-loss evidence authorizes a fresh candidate.
Persisted attempted policy ids must rotate out, and a second loss on the hold's
source route must close the fallback rather than being treated as a new one-loss
allowance.

Source-ranked runtime, locator, and watchdog route boundaries carry a
`retryable_failure` marker as well as their bounded cooldown. Policy revision
173 migrates older checkpoints that omitted this marker, so only the automatic
`reset_wait_completed=True` retry can consume the stale cooldown. A route-cap
return with incidental transit XP is not objective progression evidence and
must remain quarantined until a fresh source-safe attempt confirms a kill.

The starter's own runtime boundary raises a distinct controlled-cap signal;
do not collapse it into the transport's `asyncio.TimeoutError`. Campaign
handling must checkpoint that segment as ready and preserve its run evidence.
If the cap occurs after a confirmed objective kill, promote the terminal run
kill into campaign state, productive-policy history, research evidence, and
protection-recovery reconciliation before checkpointing. A kill recorded only
in the transcript must not be treated as a no-kill timeout or lost from the
next policy selection. The new boundary regression is offline-verified; a
fresh live cap-after-kill run is still required before calling it live proof.
Any decision wait must be clipped to the field deadline, and once the boundary
is requested the loop must wake immediately for safe healer return, save, and
quit. The outer process timeout remains a last-resort liveness guard, not the
normal route-completion mechanism.

Campaign resume also synchronizes a stale SQLite display name with the loaded
YAML contract. This is metadata repair only: preserve the existing campaign ID,
target horizon, checkpoints, and evidence, and do not create a duplicate
campaign merely because an older workspace label says `to level N` instead of
`to HERO`.

Treat a live `Char.Enemies` report as combat before utility navigation, even
when `Char.Vitals.in_combat` is still false. If DD4 sends an empty enemy packet
immediately after text containing `You are still fighting`, preserve the
text-derived combat lock through that packet; otherwise a liquidation or
healer-return route can repeat movement into combat until the watchdog charges
an XP loss. Keep the established exceptions: harmless utility attackers may
be finished only when the source-backed triviality gate passes, while an
already-requested healer return still flees. Runs 8711 and 8723 are the live
reproductions; run 8713 live-validated the first repair, and the empty-packet
repair is covered offline pending a later loot-bearing live validation.

Run 8731 showed the cost of applying the two-round source reserve to every
otherwise safe matchup: Aeloria's exact level-15 secretary fight dealt 96
partial XP before a 232-XP flee cost. Preserve the full reserve for armed,
special, multi-enemy, or unknown targets. For a single source-matched,
unarmed target at or below the character's level, with no audited special,
opponent health at or below 65%, player health at or above 50%, and one
source/observed hit covered, the starter may spend exactly one additional
between-round action before the normal withdrawal gate resumes. This is a
bounded aggression allowance, not a general health-floor reduction; it is
covered by the starter and full offline suites and still needs independent
live validation.

A reconciled research result is still evidence for the policy that produced it.
Do not treat removal of a stale result payload during startup repair as a fresh
probe of that same policy. A research handoff is fresh only when its selected
policy differs from `campaign_last_policy`; otherwise the generic source-ranked
fallback must rotate to an independent candidate or return a bounded
unavailable result. Run 8444 reproduced the stale same-policy loop, and the
repair was live-validated by run 8446, which selected the Shire Keeper route
and returned safely at the segment liveness boundary.

Source-ranked candidate ids are generated per character level. Keep prior-band
absence and crowd records for audit history, but reset-wait selection must
ignore a cooldown whose trailing candidate level does not match the current
character level. A stale level-15 cooldown must never make a level-17 frontier
appear unavailable or determine the operator-facing wait message.
The same rule applies to crowd waits: a current-band crowd remains a hard live
stop, but a prior-band crowd must never suppress an independent current-band
candidate.

When below-band evidence includes both a source mobile key and a recorded target
identity, suppress only the candidate whose normalized target identity matches
that evidence. Preserve key-only legacy records as authoritative for backward
compatibility, but never let a mismatched target name suppress an otherwise
independent source-backed candidate.

After the clean current-band and audited-special pools are exhausted, the
selector may open one research-status dynamic-wanderer probe only after the
normal no-progress threshold. Its sole autonomy rejection must be the source
classification that an aggressive useful-band wanderer can reach the route;
the candidate must have no special procedure, stay within the current level
band, and have a source peak below current HP. The generated stop remains
exact-target and isolated, so a live wanderer or other material bystander
causes a bounded crowd withdrawal rather than an unplanned fight. Keep this
as research evidence until a fresh live result proves the route. After one
meaningful successful result, allow exactly one same-reboot repeatability probe
even if recent-kill quarantine would otherwise hide it; persist a
policy-and-reboot marker before execution, then do not reopen that dynamic
route again in the same reboot. Runs 8428-8429 are the current live example.

A dynamic no-combat hazard on the randomized Shadow Grove crossing is shared
by the registered Galaxy and High Tower routes. A current-reboot result on
any one of those policies, including the older generic dynamic-hazard wording,
quarantines all registered siblings and generated candidates whose route
preflight target is `shadow guardian`. Do not reopen a sibling through normal
ordering or `--retry-stalled`; the reboot must change or a new source-backed
route must replace it.
The public `hero` command forwards this option as well. When equal-horizon
matrix manifests make a named resume ambiguous, pass the intended workspace
explicitly; equal-horizon matches remain an intentional error.

When source evidence marks a target aggressive, treat that marker as a
pre-entry gate when the candidate's minimum level fuzz is already below the
useful-XP floor (`character_level - 5`). Check both `hazards` and legacy
`autonomy_rejections`; audited special-procedure allowances must not override
this gate because an aggressive mobile can enter combat before live `consider`
returns.

DD4's `update.c` skips a plain `ACT_AGGRESSIVE` mobile when the player is more
than ten levels above the mobile's highest source-fuzzed level. Route-crowd
filters may use that cutoff to reopen a large low-level plain aggressive crowd,
but mobile attack programs and non-safe specials remain hard hazards regardless
of level. The audited special set currently admits `spec_assassin` only with a
blindness reserve and no aggressive pre-entry target, `spec_cast_druid` only
through source level 14 before fear, and `spec_cast_psionicist` only through
source level 13 before energy drain; later variants remain research-only. The
source audit records `spec_demon` spell gates through level 50, including
curse, energy drain, hold, hex, and fire breath, but the strong procedure
remains research-only until its combat and escape effects have an executable
policy.

Source area files may attach `greet_prog`, `fight_prog`, or `rand_prog` mobile
programs that issue `mpkill` directly or through `mpforce`. The candidate
parser records those commands and hard-rejects the scripted mobile or any
source companion whose program can initiate combat; an ordinary reset
companion is only trivial when no such program exists. A live loss caused by a
previously unparsed program is evidence for this parser gate, not permission
to replay the route.

An explicit operator `--retry-stalled` invocation is not proof that an area
reset occurred. It must not call a reset-consumption helper or clear active
absence/crowd cooldowns. Only the automatic retry marked
`reset_wait_completed=True` may consume reboot-local research evidence. A
safe unavailable/awaiting-reset result is the correct outcome when no other
candidate is executable.

The automatic reset wait defaults to 180 seconds, matching `HELP TICK`'s
roughly three-minute reset interval when no player is in the area; the runner
has already returned the character to healer room 3054 before waiting. Keep
the wait bounded and opt-in for capped live invocations. Do not lower it back
to a short arbitrary delay merely to make a retry appear active.
Startup repair may restore the default cooldown for a retryable result only
when that policy has no current cooldown. Preserve a lower cooldown produced
by the reset-wait aging step; reinitializing it on every invocation creates a
false stall and can repeatedly select the same unavailable route.
When an automatic retry is reached, open one bounded maintenance-only
`world-time` run to issue `time`, persist the live reboot marker, and return to
the healer before replanning. Direct `--retry-stalled` is not reboot evidence
and must not trigger this probe. If source selection temporarily consumes the
reset-aged capacity entitlement while constructing a non-executable research
policy, the maintenance probe must re-arm that entitlement and discard the
transient source candidate; only an actually dispatched field segment may
consume it. This prevents the mandatory `time` check from spending the one
capacity-isolation retry before the next invocation reaches the target.
Persist `after_segment_id` on each funding reset-history record. Startup repair
must use that boundary to rebuild only post-reset current-boot attempts and
liquidation evidence; for legacy records without the marker, locate the first
segment carrying the exact reset snapshot and infer the preceding boundary.
Older reboot history remains auditable, but pre-reset current-boot failures must
not be rehydrated as active funding blockers.
When a multi-segment invocation reaches its requested segment count, return the
last durable result before entering another reset wait. Preserve the explicit
one-segment reset-retry behavior, but never make a completed multi-segment
wrapper sleep after its final checkpoint.

If every currently admissible source-ranked target requires flight, the quoted
flight price is affordable, the shop route is not blocked, and the persisted
`magic_shop_purchase_failed` marker is explicitly cleared, allow one bounded
flight purchase even while its retry counter is positive. Otherwise the
counter can only age through productive ground XP, creating a deadlock with no
safe way to earn that XP. A true failure marker, blocked shop route, or
unaffordable price must still enter the existing funding or cooldown path. A
blocked-shop funding fallback must exclude any mobile whose same-reboot source
policy has a route hazard, source-identity mismatch, negative consider, or
incomplete/retryable, absent, crowded, or non-viable result, or fatal result;
funding is not permission to replay a quarantined route. Provision-funding
remains maintenance for selection and stall accounting, but a funding segment
that records positive XP must still decrement the flight retry cooldown; a
blocked shop plus a positive cooldown must never create an unbreakable funding
loop.

Treat a live Magic Shop refusal caused by negative reputation as a hard service
boundary. After `magic_shop_purchase_failed` and
`campaign_flight_loan_attempted` are both persisted, do not reopen the shop or
its funding route for a flight-only frontier. Return a level-scoped
`unavailable` result unless an independently executable, source-verified
non-shop route or sanctuary recovery exists; preserve the marker until a fresh
reboot or new fame evidence changes the service boundary. A bounded non-shop
fame route may still be attempted, but its health, consider, protection, and
safe-return gates remain authoritative.

Connection liveness is bounded separately from policy progress. After an
in-world command has gone silent for the inactivity interval, send one harmless
`look` probe on the existing socket before closing it; if that probe also stays
silent, close and reconnect. Connection-attempt failures are recorded and
retried at most three times. Never turn a silent socket or a connect attempt
into an unbounded wait; preserve the safe healer checkpoint when the bounded
retry is exhausted. Bind the GMCP parser to the expected character name and
discard an immortal-arrival or `Char.Base` snapshot for a different character
until the expected identity returns. Reject impossible progress (level above
HERO, negative XP-to-next-level, or a next-level threshold below current XP)
before it reaches state or campaign success. A quarantined checkpoint may
suppress same-XP live snapshots until one clean segment completes.
Every adapter `read_available` call also has a 250ms outer bound, independent
of the longer policy inactivity timer. Record `read_available_timeout`, close
and reconnect at most three times, and preserve the durable healer checkpoint
if the adapter itself blocks while reading or processing Telnet negotiation.
Every transport close is cancellation-aware and bounded to five seconds. An
interrupted worker must release its connection and storage handles promptly;
recover interrupted run records before starting another live rotation, and do
not leave duplicate campaign workers behind.

After any transport close, clear the policy's authenticated and in-world flags
and require the expected DD4 name/password/entry handshake, or an explicit
reconnecting banner, before allowing recovery, travel, or gameplay commands.
Never let a pending score, sleep, movement, or combat decision be sent to a
fresh socket while it is still at the login prompt.

Source-ranked candidate selection must compute the full source-room graph once
per distinct recall origin, then reuse that result for every candidate sharing
the origin. Keep synchronous source preparation and graph selection inside an
observable bounded startup path; repeated candidate analysis must not consume
the live segment budget or become an unreported hang.

Telnet text prompts may be split across reads, including a quiet read between
the numeric prompt body and its room suffix. Keep an incomplete `<... hits ...
mana ... move` fragment buffered through quiet reads and parse it only after
the closing prompt arrives; never let a partial prompt strand `command_in_flight`
until the segment cap. The parser and runner regressions cover this ordering,
and run 10149 reproduced it live while run 10150 validated the repair.

When one DD4 response contains text for both the room being left and the room
being entered, keep GMCP exit destinations scoped to each inferred room VNUM.
Text-only direction lists may refresh labels, but must not replace a known
destination with `None` or mix the prior room's exits into the new room. This
is required for locator-derived routes, where a lost destination can turn an
otherwise safe live endpoint into a false route failure.

Moria sanctuary recovery is source-graph gated at execution time. The deep
route to room 4152 is selected only when a strict source check proves that the
actual executed path has no reachable aggressive, scripted, or combat-special
mobile. Ordinary source-ranked routing may tolerate a below-band bystander for
an XP hunt, but that tolerance must never authorize a required-loot recovery
route. Run 12190 proved the distinction live: Moria's wandering Warrior from
room 4113 and Mage from room 4114 remained reachable on the deep path and the
route incurred 768 XP of loss. When strict proof is absent, lower-level
recovery inspects only the room-4064 reset and withdraws if the carrier has
wandered; if the shallow stop is also unavailable, return a bounded safe result
and preserve the evidence. Mages still use the bounded `cast invis` readiness
gate and every class retains the required-loot, health, consider, crowd, and
healer-return checks. Separately, the blindness-reserve handoff for audited
caster specials is class-independent: sanctuary as the opener requires
persisted `cure blindness` or two verified purple potions for every class.
When a required-loot endpoint can be entered by a source-identified wandering
hazard, the stop must issue one bounded `scan <direction>` from the immediate
predecessor before the final entry command. Resolve one-room scan reports by
target and direction against the destination-room source VNUMs; for Moria,
the explicit warrior mobile 4051 and any other source-identified mobile that
the source-safe bystander rules classify as combat-capable block entry to room
4064. The exact source carrier is exempt from this bystander check. Record a
current-reboot crowd and retryable route result, recall, and skip the endpoint
when that hazard is reported. A clear scan permits the normal exact-carrier,
crowd, consider, health, resource, and healer-return gates; an empty or
delayed scan is inconclusive and must recall. This pre-entry check does not
replace the endpoint gate after the room has been entered.

Required-loot field endpoints must resolve source-special profiles for every
observed bystander before starting combat. If a non-target mobile has an
audited post-objective hazard such as `spec_poison`, record transient crowd
evidence naming the source-registered preflight hazard and recall while still
out of combat. The sole target-first exception is the Moria deep sanctuary
route's exact source mobile 4053: when the large hobgoblin carrier is visible
in the same room, 4053 is source-proven below the useful-XP floor and has not
engaged, defer the poisoner until after the carrier. The Moria route must not
configure the generic route-gate fields for 4053: a locator result for a remote
carrier is not same-room target visibility, and it must never authorize a
poisoner kill merely to reach that room. Run 11014 demonstrated the failure
mode (a 50-XP failed-consider loss followed by a 385-XP recall loss after the
gate kill); the repaired route recalls before combat and waits for a safer
endpoint state. An engaged, ambiguous, or higher-band hazard still stops the
route; keep the late post-objective guard for hazards that arrive after combat
begins. Do not apply this exception to ordinary XP hunts.
At a source-registered required-loot reset room, if only source-known
below-band hostiles are reported and no combat exchange is observed, recall
before combat whenever recall is legal. A live `Char.Enemies` packet alone is
not an exchange; once attack text or combat state is authoritative, preserve
the existing bounded flee-and-return path.
If that pre-combat interruption is an exact source-known below-band endpoint
miss and a later source-approved carrier location remains, allow one bounded
recall to healer room 3054 and restart from the next location. Keep the
one-restart limit and retain the hazard evidence; a second interruption or
any engaged, ambiguous, or higher-band hazard remains a hard stop.
For required-loot endpoint bystanders only, complete source maps may prove an
aggressive mobile harmless when its maximum source-fuzzed level is below the
DD4 `update.c` ten-level initiation cutoff and its level window cannot join the
current fight. Missing aggression, program, special, level, or join evidence
remains a hard hazard; at level 24 this keeps Moria mobile 4050 blocked while
allowing the lower-level 4051 to be ignored.

Every source-identified field endpoint also applies the room-prose crowd gate
before `Char.Enemies` is populated. A source-indexed useful-band bystander in
the visible room causes a bounded recall; only source-confirmed below-band
bystanders may be ignored. This preserves isolation when GMCP lags the arrival
text.

Protection recovery distinguishes source-proven non-combat specials from
combat-capable procedures. A productive candidate with only a safe special
such as `spec_fido` may use one existing sanctuary reserve after a single
XP-loss record, provided it has no other autonomy rejection. Combat specials,
extra rejections, and second-loss records remain quarantined.
When that reserve route is unavailable or cooling, the same protection hold
permits up to three separately recorded ordinary fallback probes under the
low-peak, current-band, no-special, no-flight conditions above; each probe
uses an elevated 95% departure health gate, rotates to a distinct policy, and
cannot be replayed. A failed combat exchange closes the fallback; an absent,
crowded, or route-only probe consumes only its distinct-policy allowance.
Audited `spec_cast_cleric` and `spec_cast_mage` routes can blind before or
during combat. If sanctuary is not already active, require persisted `cure
blindness` training or two verified purple potions: one for the sanctuary
opener and one for recovery. Persist the runner's training capability at
segment completion so the source selector and field executor use the same
executable reserve boundary. The executor must request two source-verified
purple potions for this handoff for every class; the mage-only invisibility
requirement for deep Moria travel remains a separate route gate.
When a protection-recovery marker and negative fame coexist, block Circus,
Mirror, and Lotus combat-fame attempts even if one sanctuary potion is recorded.
Only an observation-only research policy with no kill limit may pass that
exception; combat fame must not consume the remaining protection reserve or
create more XP-loss debt.

Startup repair is a migration, not a new decision loop: repeated reconnects
must converge to the same state without metadata-only checkpoint churn. Persist
explicit same-reboot research retries separately from generic crowd history,
and treat a newer positive objective result as authoritative over older segment
evidence. Circuit-history repair must not downgrade that current-reboot positive
result merely because an older no-kill retry exists. Add a regression test and
one bounded live reconnect before claiming the repair is complete.

Poison is a hard field-combat stop. When GMCP reports an active poison-like
affect in a recallable field room, including `nausea` with `gives: poison`,
recall immediately while the character remains at or
above POS_FIGHTING; do not wait for the ordinary health floor or issue a flee
first. In no-recall rooms, use the elevated poison withdrawal floor and the
registered return route. Positions POS_STUNNED and below cannot accept recall,
flee, movement, save, or quit; wait for the server's death/Purgatory or recovery
transition and never record that state as a safe logout checkpoint. Runtime
cleanup must enforce the same rule.

Combat recall is probabilistic in DD4. Record every recall attempt and XP loss;
after a failed combat-recall message, set a route-local failure marker and do
not issue another recall on the next prompt while the same enemy remains. Take
one bounded flee or registered no-recall recovery path, audit the post-flee
room, and permit another recall only after that intervening escape state changes
or fails. DD4 also answers `God has forsaken you.` when recall is refused by a
no-recall room. When the live room flags at command issue included
`no_recall`, preserve a separate no-recall refusal marker, follow the live
return exits, and retry recall once the character reaches a different legal
room with no combat or enemies; never pay a flee penalty for that room
constraint. A refusal from a legal room remains a failed combat-recall case.
Clear both markers on confirmed room arrival or death; never turn a failed
recall into an immediate recall loop.

All character campaigns share `runs/dd4tester.sqlite3`. `RunStorage` uses a
bounded 30-second SQLite busy timeout so overlapping rotations wait for a
commit instead of failing on transient write contention. Keep the worker's
segment timeout as the liveness boundary; never replace it with an unbounded
database wait.
Each campaign runner also claims an OS-backed lease derived from its database
and campaign config before opening SQLite. A duplicate invocation must fail
immediately instead of recovering an active segment; after the owning process
exits, the operating system releases the lease and normal orphan-segment
recovery may proceed. The operator-only `recover-runs` command may also reopen
a campaign left `running` before its first segment exists, but it must respect
that same lease and leave a live worker untouched.

Named HERO resume must match the stored manifest identity, not a filesystem
directory guess. When duplicate matrix workspaces contain the same character,
select the closest stored campaign target that is at least the requested target;
if every stored target is lower, select the highest one. Equal-horizon matches
must remain an explicit error. Resuming may extend a campaign target, but must
never lower it, because matrix campaign YAML and SQLite targets are shared
validation contracts.

Maintenance fastwalks share navigation but not field-policy evidence. Store a
new maintenance route abort in `campaign_maintenance_route_hazards`, restore
source-owned target/crowd/absence/consider fields from the preceding field
policy, and clear legacy unowned markers during resume. A safe funding or
healer return must never change which progression route is retried.

Required-loot field routes must not issue `recall` while a live enemy or combat
target remains reported after the carrier is killed. Flee once, let the
post-flee audit settle, then recall; this prevents DD4's level-scaled recall
loss from interrupting corpse extraction. Keep the guard narrow to required-
loot routes so audited ordinary hazard routes retain their explicit policy.

When a bounded required-loot rotation recalls to the healer and advances to a
destination-guided stop, replay the circuit's source-registered route prefix
from the official fastwalk endpoint, then follow the source-registered VNUM
waypoints up to that stop before evaluating its first new VNUM. These are
one-use route-bookkeeping steps; do not report a missing GMCP exit or claim
progression evidence until the prefix, bridge, and live exit graph have been
checked.

Ordinary source-ranked field hunts treat source-known below-useful-band transit
attackers as one unavoidable defensive encounter: if several arrive together,
choose one, finish that current fight, quarantine the route, and return
immediately without adopting another incidental attacker. Funding and
required-loot routes remain explicit exceptions when the below-band kill is
needed to acquire coins or a declared item. When one recallable interruption
has exactly one source-known, no-special attacker, no food or water emergency,
and health above the field floor, the runner may finish that fight and resume
the current route once. A later interruption uses the bounded return path. If
the same exact source prototype re-engages on a recallable return square before
the healer return, the runner may finish one additional copy only under the
same gates. The segment permits at most two defensive fights; these kills are
not new hunting targets and are recorded separately from objective evidence.

Policy revision 186 reopens only the current-reboot Mirror Guardian result
whose route hazard was the old same-prototype Midgaard drunk flee. Policy
revision 187 reopens only the next current-reboot Mirror Guardian result whose
route hazard was the source-known carnivorous-grass interruption. Each is a
one-shot revalidation of the bounded route-resume rule; do not generalize these
repairs to other route hazards or treat either reopened policy as progression
until a fresh live result records a target kill.

The current armed-target protection boundary is narrow: when a source target
carries a weapon, its raw peak-round bound is at least half the current
character maximum HP, and live-known skills do not include `disarm`, the route
requires a verified sanctuary reserve before combat. Without that reserve the
candidate is skipped; with it, the field stop must quaff sanctuary before the
opening attack. This is a protection requirement, not a change to candidate
safety status or permission to bypass live `consider`, crowd, route, health,
resource, and healer-return gates.

When an unrelated mobile attacks during an outbound source-ranked route, the
runner may finish that bounded incidental fight, perform the normal corpse-loot
audit, and resume the saved route cursor when health, mana, movement, and food
or water reserves still pass their gates. A registered objective interception,
low-reserve result, field-stop kill, or explicitly one-way route retains its
normal post-loot recall behavior. Incidental kills remain separate from
progression evidence.

Source-ranked outbound routes may finish at most three sequential exact,
source-known, single-target, no-special, below-band transit fights when the
existing health, resource, recall, and route gates still pass. After each kill
the saved route cursor resumes; a fourth interruption, multiple attackers,
special-capable mobile, or unclassified hazard still withdraws. Legacy
fastwalks retain their one-fight boundary, and incidental kills never count as
objective progression.

Source `spec_guard` and `spec_sahuagin_guard` procedures are combat-joining
hazards even though they are not `ACT_AGGRESSIVE`: DD4's `special.c` allows them
to attack an NPC already fighting the player. Source-ranked endpoint preflight
therefore rejects a route when such a guard can reach the exact target room,
using the same level-band and crowd gates as other combat hazards. The guard
classification is endpoint-only because a transit guard cannot join until a
fight has started; it must not make every route through a city area unavailable.

Mob-loaded loot has a runtime sale value even when its area prototype cost is
zero. DD4's `E`/`G` resets call `create_object`, whose `db.c` formula
`number_fuzzy(10) * number_fuzzy(level) + number_range(1, 20)` has a ten-copper
minimum; direct ground `O`/`I` resets do not receive that value. Funding
selection may therefore accept a source-backed, releasable mobile drop using
that conservative floor, but must still reject zero-cost ground loot and must
not resolve an ambiguous duplicate name into a positive static prototype.

After a funding attempt records no kill, do not immediately replay an
unproductive candidate. Rotate to another source-safe candidate; an earlier
same-reboot carrier with any accumulated observed sale proceeds may be reused,
including partial proceeds. This exception preserves usable progress while
preventing no-kill loops when the latest candidate has produced nothing, and
the latest-attempt marker must remain candidate- and reboot-scoped.

Treat a textual DD4 `experience_lost` event as numeric progress evidence, not
only as an audit flag. Subtract its positive amount from known XP immediately,
increase XP-to-next-level by the same amount while preserving the level
threshold, and update the embedded progress snapshot. A later authoritative
`Char.Worth` packet must reconcile to that value without subtracting the loss a
second time. Checkpoints must not retain pre-loss XP merely because DD4 omitted
an immediate Worth packet.

**Current live update (2026-09-01, latest):** Kestrel remains level 24 at
334,938 XP with 31,162 XP to level 25, safely in healer room 3054 at
checkpoint 33287. Run 11061 live-validated the repaired Mirror Realm probe,
counted the opening attack, measured 30 damage against 949 target HP, and lost
385 XP on withdrawal. Runs 11062-11065 completed bounded Moria reserve, food,
sanctuary, and return-home maintenance without recovering another purple
reserve. The cure-critical selector now excludes source reset capacity above
two. Run 11066 selected the two-capacity Moria orc carrier, found it absent,
and returned safely without combat, loss, or death. Negative fame, protection
recovery, and reserve boundaries remain active. The campaign suite passes 1,058,
the starter suite passes 1,221, and the full offline suite passes 3,272 tests.
This is level-24 route and recovery evidence, not level-25, subclass, or HERO
proof.

Source-backed recovery carriers must pass both capacity gates: the selected
reset's maximum count and the number of same-mobile reset entries at the room
must each be at most two. A source reset with capacity three or more is not an
isolated reserve route even when the live endpoint appears empty, because DD4
can load same-prototype assistants before the client establishes combat
isolation. Run 11066 live-validated rotation to the remaining two-capacity
Moria orc endpoint; its current-reboot absence remains research evidence.

Clean, unarmed, one-capacity fame targets may run without sanctuary only when
both source raw peak-round and critical-hit bounds are strictly below current
maximum HP. Keep exact targeting, isolation, live consider, route, movement,
and the bounded damage-window probe; any special, armed target, route hazard,
or other autonomy rejection remains excluded. A candidate rejected only for
source peak damage still requires sanctuary and its protected bounds.

Live `practice` output is authoritative for current skill percentages.
Historical accepted or rejected training events are migration evidence only;
consume the same-level, same-reboot refresh once, retain any live route
hazard, and never replay it after it has been attempted. A trainer-only segment
that completed without a training outcome may be reopened once; a follow-up
segment containing rejections but no accepted or deferred lesson may receive one
alternate-skill refresh. Both migrations are bounded to the same character
level and reboot, and the durable deficit snapshot must be refreshed from the
latest live skill levels when the segment closes.

**Earlier current live update (2026-08-31):** Praelarran is level 15 at 106,876 XP in
healer room 3054 at the latest checkpoint 32926, with 7,924 XP to level 16. Run
10915 rotated to the independent Haon Dor Shargugh route, encountered one
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
evidence, not level-16, level-30, subclass, or HERO proof. Earlier
level-15 evidence follows. Runs
10847-10848 safely exercised the
repaired source-ranked timeout rotation. Runs 10849-10850 completed bounded
funding maintenance; run 10851 exposed a 985-XP loss on a low-band Haon route
with several source-reachable attackers. The funding selector now rejects
low-band routes with multiple static or wandering attackers. Run 10852 then
selected Katrina the Shepherd through the repaired selector, added 50 XP, and
returned safely to healer room 3054 with no loss or death. The multi-attacker
branch is offline-verified and awaits a fresh route-specific live validation.
Run 10853 performed the bounded Wyvern capacity probe; its source-registered
centaur guard was absent, so it returned without combat, XP change, loss, or
death. Run 10854 then retried Moria sanctuary recovery after its bounded reset
wait; the carrier was absent and two source-registered orcs reached room 4064
before target confirmation. The old path fled and cost 167 XP, but returned
safely. The source-reset endpoint preflight now recalls before an unstarted
exchange; this repair is offline-verified and awaits a fresh Moria live
validation. Run 10855 selected the source-ranked Haon Dor Shargugh endpoint,
confirmed its absence with `where`, and returned safely without combat or
further XP loss. Run 10856 then completed a source-ranked centaur route with
all three candidate rooms absent and no combat. Run 10857 then checked the
next bounded provision-funding endpoint; the source-selected Circus Midget was
absent, so it returned safely without combat, XP change, loss, or death. Run
10858 followed the next source-selected Ambush funding route; the fanatical
goblin guard was absent, but two source-known below-band goblin lieutenants were
unavoidable transit attackers and yielded 120 incidental XP before the runner
returned safely. No XP loss or death occurred. Praelarran is now checkpointed
at 32636.
Runs 10839-10841 completed the preceding bounded
sanctuary-recovery, Magic Shop, and Wyvern checks without combat. Kestrel is
level 24 at 336,894 XP in
healer room 3054 at checkpoint 32584. Runs 10817-10818 acquired and tested the
source-backed Moria sanctuary reserve and Mirror Realm research route without
loss. Run 10819 reached the source Beast and exposed a mixed consider response:
DD4 said both "looks like an easy kill" and "built like a tank". The old parser
entered combat and paid one 385-XP recall loss while returning safely. Run
10820 re-read the authoritative GMCP Worth snapshot and repaired the durable
checkpoint. Run 10821 then killed the source large hobgoblin for 110 XP and
returned safely with a purple reserve; runs 10822-10823 completed cure-critical
and venison-reserve maintenance without combat or XP change. Run 10825 reached
the source-registered Circus ticket clerk, received the same durability warning,
and correctly refused combat with no XP change. Run 10842 reached the Mirror
Realm moose, rejected its source-confirmed tank-like response before combat,
and returned safely without XP change. Run 10843 attempted the light-blue
flight-potion purchase, but the Magic Shop refused service because of negative
fame; the runner returned without pretending flight was acquired. Run 10844
performed the bounded `time` probe and found no new MUD reboot marker, so the
campaign remains safely parked. Serevian then completed
bounded funding rotations: run 10826 inspected the Midget endpoint without a
kill, run 10830 killed Uburz for 50 XP, and runs 10833 and 10836 killed Ushog
for 123 and 146 XP after unavoidable 10-XP Olog transit encounters. Runs 10831,
10834, and 10837 liquidated the resulting gear; all rotations returned safely
with no loss or death. The source-ranked consider
parser now treats that warning as unsupported without an explicit source peak
bound; the state reducer also reconciles GMCP-before-text and text-before-GMCP
loss ordering.
The Moria locator-backed required-loot sweep remains offline-verified and
awaits a fresh carrier-bearing live result. Run 10813 live-validated the
ordinary one-below-band-transit-fight quarantine, recording 150 incidental XP
without an objective kill, loss, or death. This is not progression proof.
Aeloria is level 18 at 165,361 XP at checkpoint 32481, Serevian is level 11 at
49,938 XP at checkpoint 32571 after the productive funding rotations, and its
next source-safe funding candidate is unavailable for the current reboot.
The current catalog-smoke Vergalcoror campaign (19) is level 8 at 30,800 XP at
checkpoint 32594 after runs 10827-10829 completed safe liquidation, return-home,
and a Circus route; run 10845 reached the Daycare ring but withdrew before the
exact target because the old wrinkled nanny was a source-registered endpoint
hazard. The older validation campaign (9) remains at checkpoint 32546. The current MUD reboot remains
`Fri Aug 14 00:15:48 2026`;
the source mirror is clean at `7996722`, and the full offline suite passes
3,189 tests. This is continuation and safety evidence, not level-30, subclass,
or HERO proof. Campaign 8 is ready at checkpoint 32584; run 10842 rejected the
Mirror Realm moose before combat and run 10843 attempted flight but the Magic
Shop refused service because of negative fame, so no flight was acquired. Run
10844 found no new reboot marker; negative fame still blocks the
Magic Shop, and the reboot-local cure-critical/fame recovery boundary still
defers the next field selection.
The latest durable checkpoint is full in healer room 3054; the historical run
10819 loss remains quarantined and has not been replayed.

Object-only source-food and required-loot stops must never call mobile-target
matching with an empty target. A food stop may accept exactly the registered
below-band transit-crowd exception only when its exact source object is
available, no route or endpoint hard hazard is present, and no additional
autonomy rejection applies. Runtime exact-object, crowd, health, resource,
recall, and healer-return gates remain authoritative; the guard is covered by
offline regression tests and live runs 10787-10801.

At levels 21 and above, the combination of protection recovery and negative
fame may admit a source-registered observation-only research probe when
sanctuary and city service are unavailable, but any viable combat promotion
must still return to the relevant sanctuary and reputation gates before a kill
is authorized.

When a long-running HERO invocation exhausts every current-reboot source-ranked
candidate, checkpoint `awaiting_area_reset` and keep the campaign `ready` so its
bounded reset retry can resume. A capped invocation must retain the explicit
`awaiting_policy`/blocked result for operator inspection; neither path may open
a segment without a fresh source-safe candidate or erase absence, crowd,
consider, protection, route, or cooldown evidence.
The source mirror remains clean at revision `7996722`. This is continuation,
liveness, and early-band evidence, not level-10, subclass, or HERO proof.

Bounded funding messages identify the exact target as completed, absent, or
attempted. A current protection marker also prevents unrelated crowd text from
masking an empty source-safe frontier, and a verified combat-pouch sanctuary
reserve now reaches the selector as usable protection; existing loss, reset,
and cooldown gates remain authoritative.

If a source-known below-band transit attacker interrupts a distant class-trainer
route, the starter emits a `training_deferred` event and returns without a
second trainer pass. The campaign stores that decision with level, reboot, and
source-refresh scoping; a later level, reboot, or source update must reassess
training rather than treating the deferral as permanent.

### Historical live continuation detail

Runs 9478-9479 created
Serevian, a fresh human male thief, through live creation and recovery. Runs
9515-9519 completed bounded maintenance without loss or death. Run 9520 then
killed six Mud School opponents for 444 XP, run 9521 added 216 XP through five
more source-ranked kills, and run 9522 added 336 XP through three more. Runs
9524-9526 added 679 XP, run 9527 completed return-home maintenance, and run
9528 added 205 XP. Runs 9529, 9531, 9534-9535, and 9537-9538 added 1,230 XP;
the intervening checkpoints were safe maintenance or reset boundaries. Run
9540 crossed Serevian to level 5; runs 9541-9543 completed level-5 setup and
handoff maintenance, run 9544 added 265 XP, run 9545 recorded an empty arena
with one bounded reset wait, and run 9546 completed return-home cleanup.
Serevian is safely level 5 at 10,436 XP and checkpoint 28829, with maximum
health 99 and mana 127. Runs 9547-9548 and 9550 added 564 XP, runs 9552-9554
added 525 XP, run 9556 added 157 XP, and run 9558 added 122 XP; the other
checkpoints were safe maintenance or bounded reset waits. Subsequent bounded
Serevian runs added 2,365 XP with safe maintenance and reset-wait checkpoints
interleaved. Run 9589 crossed him to level 6 at 14,169 XP and checkpoint 28896,
raising maximum health to 113 and mana to 134. Runs 9590-9613 then completed
bounded level-6 outfit, recovery, and source-ranked rotations; productive routes
added 955 XP while empty or absent candidates stopped safely. Run 9613 left
Serevian at 15,124 XP and checkpoint 28948, full in healer room 3054. Praelarran
run 9598 added 502 XP through Fleshmonger; runs 9599-9612 completed safe
liquidation, protection, and healer-return maintenance. He is level 13 at 76,029
XP and checkpoint 28951, full in healer room 3054. Runs 9614 and 9615 then
tested another Circus route and the Dwarven Daycare route safely without
forcing combat; the latest Serevian checkpoint is 28948. Praelarran run 9598
added 502 XP through Fleshmonger, and runs 9626-9628 added another 450 XP
through the current-band pool. His latest pre-repair field checkpoint was
29331; runs 9798-9802 then completed bounded sanctuary, secretary, Shadow Keep,
crowd, and Ambush continuations without death or XP loss. Run 9799 killed
source mobile 3142 for 269 objective XP and run 9802 killed source mobile 4512
for 338 objective XP. Praelarran is safely level 14 at 94,450 XP in healer
room 3054 at checkpoint 29475, 3,650 XP short of level 15. Runs
9681-9682 crossed level 14 and completed liquidation. Run 9686 exposed a
text-only `The Temple Square` room header without a GMCP VNUM; the runner
cleared stale identity and aborted safely. `StarterPolicy` now resolves unique
source-backed Midgaard room names when GMCP omits the VNUM. Run 9687 crossed
the repaired handoff but paid a 148-XP health-floor withdrawal; run 9689 then
completed a clean 288-XP archer route. Runs 9690-9692 then added 665 XP through
Haon, Shadow Keep, and Plains North with no loss or death; the campaign is ready
at the next source-ranked boundary. Runs 9699-9701 then added 80 XP through Haon,
Shadow Keep, and Midgaard without loss or death; the campaign is ready again at
the next source-ranked boundary. Runs 9702-9704 then added 601 XP through Shire,
Shadow Keep, and Fleshmonger without loss or death. Runs 9705-9707 then completed liquidation,
return-home, and sanctuary recovery without changing XP or recording loss or death.
Runs 9708-9710 then added 411 XP through Shire, Haon, and Shadow Keep without
loss or death. Runs 9711-9713 then added 607 XP through Shire and Shadow Keep
and completed provision restock without loss or death.
Runs 9714-9716 then added 271 XP through Fleshmonger and completed safe return
and liquidation. Runs 9717-9719 then added 130 incidental XP without a
source-objective kill and completed safe healer recovery. Runs 9720-9722 then added
620 XP, including a source-objective Shire kill, without loss or death. Runs 9723-9725 then added 316 XP through Shire and completed Fleshmonger and Dwarven Daycare segments without loss or death. Runs 9726-9728 then added 378 XP, including a source-objective Shire kill and safe sanctuary recovery. Runs 9729-9734 then added 496 XP; run 9733 killed source mobile 4512, The vile goblin, for 346 objective XP, with the remainder incidental transit XP. Runs 9735-9740 then added 437 XP; run 9736 killed source mobile 4512 for 50 objective XP, run 9737 killed source mobile 139, Sir Durok of EAT, for 377 objective XP, and run 9735's 10 XP drunk was incidental. Runs 9741-9746 then added 1,047 XP; run 9741 killed source mobile 4512 for 307 objective XP, run 9743 killed source mobile 139, Sir Durok of EAT, for 396 objective XP, and run 9744 killed the goblin lieutenant incidentally for 80 XP and source mobile 4512 for 264 objective XP. Runs 9747-9752 then added 1,079 XP; run 9748 killed source mobile 139, Sir Durok of EAT, for 431 objective XP, run 9750 killed source mobile 4512 for 50 objective XP, and run 9751 killed source mobile 139 for 488 objective XP, with 110 incidental XP alongside them. Praelarran is alive and loss-free in healer room 3054 with no stalled segment or orphan worker, and is 6,225 XP below level 15. This is level-14 continuation evidence, not level-15, subclass, or HERO proof. Runs 9480-9481 completed Praelarran's
liquidation and healer return without XP change. Run 9482 added 437 source XP
from Shire; run 9483 found sanctuary recovery absent; run 9484 rejected a
crowded secretary route without combat; run 9485 withdrew at the hard health
floor with 34 incidental XP and no loss; and run 9486 added 452 objective XP
from the Shire receptionist. Runs 9487-9488 safely recorded Circus and Moria
no-target probes. Praelarran is now 6,225 XP below level 15. The public HERO
credential boundary now allows an untouched prepared workspace to generate its
first stored password, while an already-recorded campaign stays strict about
missing credentials.
Run 9757 then reproduced a Gremlin Lair recall-recovery hazard: the first
recall reached Temple room 3001, but stale GMCP identity discarded the
following inferred text room event and a second recall cost 148 XP. No death or
objective kill was recorded. Revision 174 now accepts the authoritative room
transition and persists the route as a retryable current-reboot hazard. Run
9758 converted the failed checkpoint during startup migration and completed
safe return-home; Praelarran is 6,373 XP below level 15. Treat this as the
authoritative current status; the longer run block below is historical.
Runs 9759-9788 then added 1,507 objective XP across five source-matched kills,
plus bounded incidental combat and maintenance. Run 9787 reached the
120-second field cap and recovered cleanly; run 9790 recorded a 148-XP
Gizmo-route recall loss without a death or objective kill, and run 9791
restored full healer state. Runs 9792 and 9795 then recorded separate -148 XP
losses on the Fleshmonger and Moria routes; their one-loss quarantines held,
and run 9797 completed flight maintenance. Runs 9798-9802 then exercised
bounded sanctuary recovery and source-ranked fallback rotation: Moria's carrier
was absent, Shadow Keep was absent after incidental wandering combat, the
secretary yielded 269 objective XP before its crowd repeat was skipped, and the
vile goblin yielded 338 objective XP after live consider passed. The selector
now prefers recent productive routes over low-fuzz fresh candidates; the full
offline suite passes 3,013 tests. Praelarran is 3,650 XP below level 15.
The source-ranked selector may accept a source-proven noncombat special when
the parser emits no autonomy-rejection string, as well as the legacy synthetic
rejection form. This representation rule does not bypass special-safety,
source-identity, consider, health, resource, or recovery gates. The complete
offline suite passes 3,012 tests. Maintenance policies may reopen after a
historical completion marker when the corresponding live need is newly
observed; this remains bounded by the need flag and normal safety gates. These
are continuation proofs, not level-13, subclass, or HERO evidence. The longer
block below is historical context.

Historical live continuation anchor for 2026-08-25: Praelarran is level 15 at
104,227 XP, checkpoint 30224, and safely in healer room 3054. The last
productive run was 10036; the subsequent empty-funding invocation is now a
ready `provision_funding_unavailable` checkpoint rather than a failed campaign.
Aeloria is level 18 at 165,613 XP, checkpoint 30219, and Serevian is level 6 at
15,268 XP, checkpoint 30222; both are safely in healer room 3054. The full
offline suite passes 3,031 tests, only the Discord streamer remains outside
the normal shell, and no campaign worker is running. This is live continuation
and liveness evidence; no subclass or HERO proof is claimed.

Historical campaign anchors:
Serevian is
level 6 at 15,268 XP (checkpoint 30222) and is also safely in healer room 3054;
Aeloria is
level 18 at 165,613 XP (checkpoint 27725); Dorrik is level 24 at 363,330 XP
(checkpoint 28574); Kestrel is level 24 at 336,913 XP (checkpoint 26810);
Corararfen is level 6 at 17,020 XP (checkpoint 27756 after runs 9121-9123);
Velnor is level 6 at 15,471 XP (checkpoint 28565; cure light trained);
Fenanallor is level 4 at 7,771 XP (checkpoint 27767 after runs 9128-9129;
shoot trained).
No DD4Tester worker is running, and
the full offline suite passes 3,031 tests. The Telnet read path now reduces
authoritative GMCP room transitions before same-read text, and startup
reconciliation preserves the newest maintenance-attempt level. Runs 9109-9110 requested a live
Suturb retrieve quest, then exposed a non-kill quest route that followed a raw
shortest path into Old Marsh room 8310. Source mobile 8306, the aggressive
level-12 huge hairy beast, attacked there; Aeloria fled at 193/218 HP, lost
232 XP, and recovered safely without dying. The repaired quest preflight and
executor now use the source-safe route gate for retrieve, object, and hoard
targets; source validation rejects room 8310 at level 18, and the regression
suite covers the boundary. Direct live proof of the repaired quest route awaits
the next generated non-kill quest. Runs 9029-9033 exposed and repaired
Runs 9112-9113 completed Dorrik's provision-funding loop without XP change,
death, or loss. Runs 9114-9120 added 1,304 XP to Praelarran through four
source-matched warrior kills, with no loss or death; he is now 13 XP short of
level 9. Runs 9121-9123 completed Corararfen's outfit, return-home, and
daycare-ring recovery maintenance without a field loss. Runs 9124-9125 added
109 XP to Velnor through a source-matched Sorbus kill and trained cure light;
the later fanatic route was absent. Runs 9128-9129 completed Fenanallor's
ranger starter/Mud School boundary, added 227 XP from two boars and two wolves,
and trained shoot; the next invocation remained safely inside that boundary.
Run 9130 then advanced Praelarran from level 8 to 9 through a 192-XP Illusionist
kill, recovering a shimmering key and 21 maximum HP without loss or death.
Run 9132 then added 835 XP from three source-matched level-9 kills, recovered a
disarmed broadsword and 14 items, and trained enhanced damage plus unarmed
combat knowledge for stun; no loss or death occurred.
Run 9137 then added 681 XP from the on-duty guard and cook, recovered eight
items including a rearmed broadsword, and returned safely without loss or death.
Run 9147 then added 494 XP from two more guard/cook kills, recovered ten items
and a disarmed broadsword, and returned full without loss or death.
Runs 9141-9142 then added 200 XP to Dorrik from the large hobgoblin and blonde
dwarf, recovered a purple sanctuary potion, and used it on the second route;
he returned full without loss or death. Run 9153 then added 485 XP to
Praelarran from the source-matched on-duty guard and cook after a trivial drunk
contact, recovered seven items, and returned full. Runs 9154-9155 completed
loot sale and return-home maintenance. Campaign resume synchronized his stale
`to level 10` SQLite label to `Praelarran to HERO` without changing Campaign 30
or its checkpoints. Runs 9156 and 9158-9159 added 1,367 XP through
armed-guard, bull, and guard/cook kills; run 9157 recorded a safe Moria absence.
Runs 9160-9161 completed return-home and Plains North/Sorbus absence maintenance.
Runs 9162-9169 added a further 1,023 XP through a Shire bull and three
guard/cook rotations without death or XP loss. Run 9187 crossed Praelarran
from level 9 to 10 with 519 XP and 23 maximum HP. Run 9191 visited the
level-10 warrior trainer, read the guildmaster plan, trained enhanced damage to
44%, and added 640 XP from the patrolling guard and cook's boy after recovering
a disarmed broadsword. Runs 9194-9195 trained enhanced damage to 49% and
unarmed combat knowledge to 41% toward the source-backed stun prerequisite.
Runs 9198-9218 added 4,456 XP through source-matched warrior kills and safe
Moria, Shire, and Circus rotations; run 9219 sold the recovered loot, runs
9220-9221 recorded clean absences, and run 9222 added 828 XP from three
source-matched kills. Praelarran is safely checkpointed at level 10 with
45,728 XP and no loss or death. Runs 9225-9226 then added 1,142 XP through an
armed-guard kill and three source-matched Fleshmonger kills; run 9227 sold the
loot, and runs 9228-9229 recorded clean Cult absences. Praelarran is now safely
checkpointed at level 10 with 46,870 XP and no loss or death. Run 9239 then
crossed Praelarran from level 10 to 11 with 771 XP from two source-matched
guard kills and 22 maximum HP, returning safely without loss or death. He is
now checkpointed at level 11. Runs 9242-9243 continued the warrior trainer route,
raising enhanced damage to 53%; run 9244 added 507 XP and trained unarmed combat
knowledge to 47% toward the 60% stun gateway. Runs 9247-9249 included a clean
Circus probe, flight maintenance, and a further 255-XP small-troll kill. Run
9250 then added 582 XP from two source-matched guards and recovered 12 items.
Praelarran is safely checkpointed at level 11 with 50,804 XP and no loss or
death. Runs 9254, 9259, and 9262 added 536 XP from three small-troll kills; runs
9255 and 9263 added 1,220 XP from four source-matched guards, with safe Moria
and Shire absence probes between them. Praelarran is now safely checkpointed at
level 11 with 52,560 XP and no loss or death. Run 9267 added 230 XP from an
armed guard. Runs 9268 and 9280 added 864 XP from source-matched patrolling
guards; run 9272 added 202 XP and run 9278 added 186 XP from small trolls. Run
9274 killed a patrolling guard for 395 XP, withdrew at the 32% health floor, and
paid a 99-XP flee cost for a net 296 XP; the exact source policy is now bounded
by its one-loss protection rule. Run 9277 added 302 XP from an armed guard,
while run 9279 recorded a clean Circus absence. Praelarran is safely
checkpointed at level 11 with 54,650 XP and no death. Runs 9283-9284 added
468 objective XP from an armed guard and a small troll. Run 9285 recorded a
clean Strongman's Tent no-target result; run 9286 added 401 XP from a patrolling
guard; runs 9287-9288 completed loot sale and return-home maintenance. Run 9289
added 178 XP from an armed guard and used its body part as food; runs 9290-9291
completed flight and return-home maintenance. Run 9292 added 178 XP from a small
troll, run 9293 recorded 10 incidental XP from a drunk while its Circus target
was unavailable, and run 9294 added 342 XP from a patrolling guard after
recovering a weapon dropped by a live disarm. Praelarran is now level 11 at
56,227 XP at checkpoint 28226, with no loss or death in this continuation batch.
Runs 9297-9298 added 490 objective XP from an armed guard and a small troll;
run 9299 recorded a clean Strongman's Tent no-target result; and run 9300 added
281 XP from a patrolling guard with six items recovered. Praelarran is now
level 11 at 56,998 XP at checkpoint 28243, with no loss or death in these
follow-up segments.
Runs 9303-9306 added 789 objective XP and 20 incidental XP through armed-guard,
small-troll, Circus absence, and patrolling-guard routes. Runs 9307-9308
completed loot sale and return-home maintenance; run 9309 added 202 XP from an
armed guard; run 9310 refreshed flight; run 9311 recorded a 10-XP incidental
drunk contact while the Cult fanatic was unavailable. Run 9312 then added 442
XP from a patrolling guard and crossed Praelarran from level 11 to 12, raising
maximum health from 246 to 270. He is now level 12 at 58,461 XP at checkpoint
28275 with no loss or death.
Runs 9313-9316 completed loot sale, healer return, outfit, and return-home
maintenance; a 10-XP transit contact occurred during the sale without an
objective target, loss, or death. Run 9317 then killed the source-matched
on-duty guard for 241 XP, recovered six items, and preserved an enhanced-damage
practice when the trainer's current proficiency cap rejected another attempt.
Praelarran is now level 12 at 58,712 XP at checkpoint 28287, with no loss or
death.
Runs 9318-9319 completed loot sale and healer return. Run 9320 accepted second
attack at 40% toward its 50% cap; run 9321 refreshed flight. Run 9322 completed
a bounded Moria search with only 20 incidental XP and no objective kill, while
run 9323 raised unarmed combat knowledge to 50% toward the 60% stun gateway.
Run 9324 then killed the patrolling guard and on-duty guard for 583 objective
XP, recovering 11 items. Praelarran is now level 12 at 59,315 XP at checkpoint
28306 with no loss or death.
Runs 9325-9326 completed loot sale and healer return. Run 9327 added 192 XP
from an armed guard; run 9328 recorded the Dragon Cult fanatic absent; and run
9329 reached the Shire route and skipped a crowded circuit target before combat.
Run 9330 then killed the patrolling guard and on-duty guard for 477 objective
XP, recovering 11 items. Praelarran is now level 12 at 59,984 XP at checkpoint
Runs 9333 and 9338 recorded clean Circus and Dragon Cult absences. Run 9334
added 214 XP from an armed guard; run 9335 added 738 XP from a patrolling guard
and on-duty guard after recovering a disarmed broadsword; runs 9336-9337
completed loot sale and healer return. Run 9339 added 229 XP from another armed
guard. Praelarran is now level 12 at 61,165 XP at checkpoint 28347 with no loss
or death.
Run 9340 recorded a clean Circus absence. Run 9341 added 543 XP from a
patrolling guard and on-duty guard; run 9342 recorded a 10-XP incidental drunk
contact during loot sale; and run 9344 added 182 XP from an armed guard. Run
9345 recorded another clean Circus absence, while run 9346 added 269 XP from a
patrolling guard and skipped a crowded second target. Run 9349 added 318 XP
from an on-duty guard; run 9352 added 280 XP from an armed guard; run 9353
recorded a clean Circus absence; and run 9354 added 284 XP from an on-duty
guard. Intervening maintenance returned safely. Praelarran is now level 12 at
63,051 XP at checkpoint 28390 with no loss or death.
Runs 9355-9356 recorded safe Daycare and Cult absences. Run 9357 added 271 XP
from an on-duty guard; run 9358 added 175 XP from a Shire bull after skipping a
crowded circuit; and runs 9359-9360 completed flight and return-home
maintenance. Runs 9361, 9364, and 9367 recorded clean New Ofcol absences; run
9362 added 228 XP from an on-duty guard; and run 9363 recorded a clean Circus
absence. Run 9368 added 174 XP from an armed guard. Run 9369 then exposed an
unexpected dwarf-forest combat, costing 116 XP on withdrawal without death; the
exact route is now bounded by the current-reboot loss policy. Praelarran is now
level 12 at 63,783 XP at checkpoint 28435, safe and with no death.
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
Aeloria's next bounded invocation retained her Shadow Keep crowd gate without
combat. Runs 9029-9033 exposed
and repaired
a GMCP-only post-objective pursuer ordering defect, then recorded a bounded
nomad withdrawal, a Giant Eel kill for 866 XP, and a safe Moria
large-hobgoblin kill for 90 XP. Runs 9034-9035 completed crowded/absent
Shadow Keep and Crystal routes without loss. Run 9033 did not reproduce a
pursuer after the carrier died, so direct live trigger proof remains pending.
Run 9041 completed a bounded Shadow Keep eel continuation without combat, XP
change, death, or loss. Run 9042 requested a live retrieve quest; source
preflight proved Gloomy Forest room 285 inaccessible from Midgaard. Run 9043
returned to Suturb and issued `QUEST ABORT` without combat, XP change, death,
or loss; run 9044 then completed one automatic reset wait and recorded a clean
Shire absence. Run 9045 completed a bounded source-ranked hunt without
progress; run 9046 applied the source-identity gate; and run 9047 recorded the
next funding target absent at its source room. All three had no combat, XP
change, death, or loss. Run 9048 then killed the source-matched large orc in
Moria for 175 XP and two items, returning Praelarran safely to healer room
3054. Run 9049 then killed the source-matched Shire Miller for another 115 XP
and recovered a heart, again returning safely. Runs 9050-9051 then added 125
XP from a Shire bull and 161 XP from two Circus kills; five items were recovered
in the latter run. Run 9052 extracted purse coins and discarded the empty
container; run 9053 recorded a safe Circus absence; run 9054 then reopened
Moria for another 182-XP large-orc kill and two items. Runs 9055-9057 then
added 68 XP from a Circus bearded lady, 92 XP from Sorbus the Hermit, and 190
XP from a fanatic monk. Run 9058 sold three rings for 23 coins and returned
Praelarran safely to the healer. Run 9067 then killed a source-matched Shire bull
for 170 XP, crossing him from level 7 to level 8 with 19 additional maximum hit
points and no loss or death. Run 9068 filled the last legal empty wear slot,
hands, with a verified basic Leather Shop item; run 9069 completed healer recovery
without XP change. Praelarran remains safely checkpointed in room 3054. Run 9070
then trained enhanced damage and unarmed combat knowledge for the source-backed
stun prerequisite, killed Ivan and the Illusionist for 335 XP, and returned
without taking damage or losing XP. Run 9071 rejected the live receptionist
after `consider`; an aggressive wandering drunk attacked during transit and was
finished defensively for 10 incidental XP, with no objective target claimed.
The return remained safe. Run 9072 then recorded the fanatic route absent with no
combat, XP change, loss, or death. Run 9073 rotated to the Circus and confirmed
Ivan plus the Illusionist for 320 XP, with full health and a safe healer return.
Run 9074 then killed the source-matched cook for 368 XP, recovered two items,
and returned at full health. Run 9075 then recorded the Circus midget route
absent with no combat, XP change, loss, or death. Run 9076 confirmed Ivan plus
the Illusionist for 403 XP, with no loss or death and full healer recovery.
Run 9077 recorded the fanatic route absent with no combat, XP change, loss, or
death. Run 9078 then killed the source-matched cook for 429 XP and two items,
returning at full health. Runs 9079-9080 then sold four recovered items for 164
coins through the verified Weapon Shop, Leather Shop, and Armoury, followed by
safe healer recovery without XP change. Runs 9081-9082 then added 786 XP from an
armed guard and Ivan; the second run skipped an ambiguous target and tried the
recovered body part as food. Both returned safely without XP loss or death.
Runs 9083-9084 then recorded the fanatic route absent and a source-matched cook
kill for 275 XP and two items, again returning at full health. Runs 9085-9086
then added 739 XP from Ivan and an armed guard, with no loss or death and safe
healer returns. Runs 9087-9088 then recorded a fanatic absence and skipped an
ambiguous strongman target; an aggressive drunk was finished defensively for 20
incidental XP, with no objective target, loss, or death. Runs 9089-9090 then
added 614 XP from a Bearded Lady, Illusionist, and armed guard; one wandering
drunk added 10 incidental XP. Both returned safely without loss or death. Runs
9091-9092 then covered the Foundry loop, recovering a disarmed broadsword and
selling six items for 103 coins through the Leather and Weapon Shops. Run 9093
completed a safe return-home checkpoint; run 9094 then added 120 XP from a
source-matched Bearded Lady without loss or death. Run 9095 confirmed the
Dragon Cult fanatic absent and returned safely; run 9096 then killed source
mobile 112, Ushog, for 238 objective XP after a 20-XP incidental Olog contact,
recovered five items, and returned full to healer room 3054. Run 9097 sold
three items for 26 coins through the Armoury and Jeweller after an aggressive
drunk was finished for 10 incidental XP; run 9098 slept and completed a safe
healer return. Runs 9099 and 9100 then reached two Circus source rooms, found
the Bearded Lady and mother targets absent, and returned safely without combat,
XP loss, or death. Runs 9101-9102 then killed the source-matched Illusionist
and Ivan for 250 objective XP, recovered two keys, and recorded the Dragon Cult
fanatic absent; both returned safely without loss or death. Run 9103 then added
141 XP in the Foundry: Olog supplied 10 incidental XP and source mobile 112,
Ushog, supplied 131 objective XP; five items were recovered. Run 9104 sold
three items for 41 coins through the Leather Shop and Jeweller. Run 9105
completed healer recovery; run 9106 then killed source mobile 2405, Katrina the
Shepherd, for 269 objective XP and two items after a safe consider, reaching a
71.7% HP low point before safe recovery. Run 9107 recorded the Circus midget
absent; run 9108 bought and verified a light blue flight potion from the Magic
Shop without combat or XP change. Dynamic quest candidates now
reuse the ordinary source ranker
with exact reset-room matching and current level/HP, special, companion, and
route gates; the actual advancement thresholds remain the `update.c` values
29, 49, 79, and 99 despite stale level-69 display text in `act_info.c`. An
unsafe active quest or source-proven inaccessible quest room now selects a
bounded `quest abort` return to its registered questmaster, then preserves
DD4's cooldown before a replacement request. The generic selector and executor
keep gas-bearing breath forms research-gated even when damage, sanctuary, and
health reserves are proven; lightning breath retains its separate
source-bounded path and lower nominal targets retain the ordinary ceiling.
The generated-quest candidate path now also mirrors `quest.c`'s nominal target
ceilings of +4, +9, +14, and +19 by level band. This wider level allowance is
never applied to ordinary hunts and remains behind the shared source route,
HP, special, companion, crowd, and live-consider gates; source-ineligible
mobile flags and shopkeepers are rejected before movement.
For a wandering target reported away from its reset room, require the source
wander graph to reach that exact live room, rank a temporary endpoint there,
and use its source-safe route; do not fall back to a raw shortest path.
Runs 9014-9015 completed bounded continuations without death or XP loss: Aeloria reached a source-registered
Arachnos route and withdrew on its poisonous-bystander gate, while Praelarran
confirmed a Circus target absent. Run 9016 completed Dorrik's automatic reset
retry and safe Magic Shop flight maintenance; runs 9017-9019 then added 67,
122, and 176 objective XP for Praelarran from source-matched routes and returned
him safely to the healer after each segment; run 9020 added another 134
objective XP, and runs 9021-9024 recorded two source absences, flight
maintenance, and safe return-home without loss. The campaign repair now
re-arms a timed-out source route only after an automatic reset wait, consumes the retry
when the hunt segment opens, carries legacy attempt counts forward, and
quarantines the route after two bounded attempts. Campaign preflight also
records the exact source teacher mobile, room, keyword, skill, and route for all
18 legal subclass combinations; the subclass-focused checks pass 78 tests.
The class-independent audited-caster handoff requires a second verified purple
or trained cure before reopening a caster-special route. A bounded Dorrik
invocation preserved the current-reboot Tentusks crowd gate, so no live reserve
handoff was claimed. This remains continuation and source-preflight evidence,
not level-19, level-30, subclass-transition, or HERO proof.

Runs 8964-8978 live-validated the level-18 source-frontier rotation. Shadow Keep
recorded a crowded endpoint, Wyvern and Hood were absent, Moria and Crystal
were absent, Dwarven Home was not useful on `consider`, and flight maintenance
completed safely. Run 8978 confirmed Giant Eel mobile 16602 in room 16610,
passed `consider`, and completed the 1,089-XP kill with no death or new loss.
The earlier runs 8928-8963 live-validated the level-18 funding, protection, retry, and
recovery boundaries. The Gnome Treasury stash yielded 719 copper and enabled
flight; Arikasbab cost 139 XP, a bounded Town Clerk `spec_thief` probe cost 166
XP, and run 8957 exposed the unsupported-health Secretary loss at live 319 HP
versus Aeloria's 218. Run 8958 recovered her in healer room 3054; run 8959
then found a Wyvern target absent and returned full with no new loss. Runs
8953-8955 checked Crystal and Dwarven Home crowd gates. Run 8962 confirmed a
source-ranked Keeper kill, acquired the tower key, and returned full without
XP change; run 8963 safely rejected an Arachnos Queen Spider endpoint crowded
by three poisonous spiders. DD4 `fight.c:group_gain` awards no XP when a
summoned NPC delivers the final blow, so the source-ranked mage familiar path
now orders the pony to flee at or below 45% target HP. The guard has focused
offline regression coverage; these remain continuation records, not level-10,
subclass, or HERO proof. Resume from checkpoint 27295 toward level 19.

The latest bounded rotation validated the level-24 source frontier and startup
repair. Run 8866 bought flight; runs 8867 and 8871 added only safe incidental
rabbit XP, while runs 8868-8870 recorded absent source targets. Run 8872
exposed a randomized Mirror Realm inter-target watchdog and returned safely
with no XP loss. Runs 8873-8875 completed safe return and bounded Mirror
probes without death or loss. Aeloria's run 8876 safely exposed a delayed
text/GMCP transition boundary during provision funding; run 8877 replayed it
successfully after the parser repair, and runs 8878-8879 completed liquidation
and healer return. The parser emits a GMCP room refresh only when text has
identified a transition and cleared the prior exit graph. The state reducer
still preserves GMCP destination VNUMs and ignores delayed text that conflicts
with a confirmed room. Source-ranked randomized inter-target legs use the
source-safe live-maze graph rather than replaying fixed VNUMs. This is
class-coverage, liveness, and repair evidence, not HERO proof.

When text and GMCP room events arrive out of order, never let a text VNUM move
the reducer backward or erase known GMCP exit destinations. For source-ranked
randomized circuit legs, retain the static route only as a preference and use
the live GMCP VNUM graph with bounded abort/recovery behavior.

Runs 8759-8809 are the latest bounded continuation evidence. Run 8759 bought a
135-copper flight potion and live-validated text-only room-VNUM recovery on the
return to healer room 3054. Run 8760 recorded an absent white stag and returned
without XP change. Run 8761 located the Arachnos guardian through `where`, but
the reported Realm of Hopeless location was not a reachable combat endpoint
before the progress watchdog, so it returned safely without XP. The locator
repair now rebases matched source routes from the live room instead of
concatenating unrelated circuit waypoints; it is covered offline, while a
fresh live guardian target remains pending because the current-reboot absence
cooldown is still active. Run 8762 then killed the source-matched Fat Black Cat
(mobile 28311, room 28316) for 682 objective XP and returned safely with no XP
loss or death. Run 8758 is a
negative safety result: repeated fleeing from a level-8 dustdigger in the Great
Eastern Desert return maze caused death, followed by successful corpse and
Purgatory recovery. Run 8763 then killed the source-matched giant, purple sand
worm (mobile 5004, room 5028) for 592 objective XP, but lost 1,392 XP to
repeated flee penalties from below-band dustdiggers while returning; Aeloria
still reached the healer alive and full. The delayed-pursuer assessment repair
is offline-verified and awaits a fresh live maze target; do not call these runs
HERO proof. Run 8764 then completed the normal Moria sanctuary continuation,
killed the source-matched large hobgoblin for 100 objective XP, and returned
full to healer room 3054 without XP loss or death. Run 8765 then found no
objective nomad kill; a source-known below-band drider interruption yielded 80
incidental XP without XP loss or death, and Aeloria returned safely. Run 8766
then completed a return-home maintenance segment with no XP change, death, or
unsafe state, preserving the healer-room checkpoint. Run 8767 then completed
safe loot liquidation with no XP change, death, or XP loss. Run 8768 then
completed another return-home maintenance segment with no XP change, death, or
XP loss, preserving the full healer-room checkpoint. Run 8769 then completed
the source-priced flight-potion maintenance step without XP change or combat.
Run 8770 then used `where` to confirm the white stag absent, returned safely,
and recorded no XP change, death, or loss. Run 8771 then found three mobiles in
the Dwarven Home room, recorded a source-backed crowd gate, and withdrew without
combat, XP change, death, or loss. Run 8772 then found two mobiles in the
Dwarven Home servant room, recorded the same source-backed crowd gate, and
withdrew before combat without XP change, death, or loss. Run 8773 then reached
the source-present Keeper of the Tower, withdrew at the 51% health gate after
missed mage damage, and paid 232 XP without a kill or death; this exact policy
is quarantined rather than blindly retried. Run 8774 reached the Forest
medicine route but hit the 180-second boundary and returned safely without an
objective kill, required item, XP loss, or death. Run 8775 then completed the
safe return-home maintenance boundary with no XP change, loss, or death. Run
8776 then confirmed the gang/hood target absent at room 2148 and returned safely
without combat, XP change, loss, or death. Run 8777 then confirmed the
wyvern/centaur target absent at room 1717 and returned safely without combat,
XP change, loss, or death. Run 8778 found Essabella present at room 4528 but
below the useful-XP floor, skipped her before combat, and returned safely
without XP change, loss, or death. Run 8779 then killed the source-matched
giant, mobile 6506 in room 6508, for 376 objective XP and returned full without
XP loss or death. Run 8780 then retried the same source VNUM after a fresh
respawn, found the giant materially healthier, withdrew at 85/218 HP, and paid
232 XP; the exact policy is quarantined for this reboot rather than replayed.
Run 8781 then completed the source-backed provision loop, killing valley elf
sentry mobile 7804 for 60 XP under the registered below-band funding exception
and returning full without XP loss or death. Run 8782 then completed safe loot
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
source-matched Sergeant at Arms' Secretary again, but the mage's damage remained
insufficient; Aeloria withdrew at 46% health, paid 118 net XP, and returned
alive and full to healer room 3054. The exact combat policy is quarantined
rather than replayed. This reinforces the next engineering priority:
source-backed mage damage, protection, and training decisions, not a lower
withdrawal floor. The poison-name repair remains offline-verified and awaits a
bounded live Moria revalidation.

Run 8802 confirmed the white stag absent and returned safely without combat,
XP change, loss, or death. Run 8803 then entered the source-matched
foreign-trade representative room, whose arrival text visibly contained three
bodyguards. The pre-patch endpoint did not apply the room-prose crowd gate
while `Char.Enemies` was null; combat began, the bodyguards joined, and Aeloria
lost 282 XP in aggregate (153 damage credit offset the losses for a 129-XP net
drop) before returning safely. The repaired gate now counts source-indexed
room mobiles before GMCP enemy data exists and is covered by the offline suite.
Run 8804 then killed source mobile 28311, the Fat Black Cat in room 28316, for
791 objective XP and returned full without XP loss or death. Direct live
revalidation of the new room-prose gate and the earlier poison-name repair
remains pending; the next engineering priority is source-backed mage damage,
protection, and training decisions. Run 8805 then completed the normal Moria
sanctuary-carrier route, killed the source-registered large hobgoblin for 100
objective XP, recovered another purple potion, sacrificed the empty corpse,
and returned full to healer room 3054. Aeloria is now at 158,276 XP with no
loss or death. Run 8806 then searched the source-allowed Hood circuit, found
the target absent, and returned safely through healer recovery without XP
change, loss, or death. The campaign remains ready for the next frontier
selection. Run 8807 then resumed Praelarran from the explicit authoritative
validation workspace, killed the source-matched Bearded Lady for 92 objective
XP, collected its hairy key, sacrificed the empty corpse, and returned full to
healer room 3054 without XP loss or death. This extends generic warrior
continuation evidence but is not level-10, subclass, or HERO proof. Run 8808
then resumed Corararfen from campaign 22, killed the source-matched Bearded
Lady for 68 objective XP with `cause serious`, handled Beastly Fido as a
non-combat joiner, and returned safely without XP loss or death. This extends
cleric continuation evidence but is not level-10, subclass, or HERO proof. Run
8809 then searched Corararfen's independent Circus Bobby route, found the
approved target absent, and returned fully recovered without XP change, loss,
or death. The level-10 cleric campaign remains ready for the next reset-aware
selection.

When a source-ranked hunt returns through a no-recall maze, distinguish an
attackable hunt from an all-consider-only research probe using the registered
hunt stops, not only the transient `fastwalk_attack_started` flag. If every
live pursuer is at least five levels below the useful-XP floor and no food,
water, or poison emergency is active, a real hunt may fight one bounded
interruption while above the 15% hard return floor; a research-only probe must
continue its flee-and-return path. This prevents repeated flee XP penalties
without turning research probes into opportunistic hunts. If combat text arrives
before `Char.Enemies`, wait for one bounded GMCP turn before issuing another
flee; this prevents a stale packet gap from becoming an avoidable XP loss while
retaining the worker liveness boundary.

The runtime logout boundary is healer-safe: at room 3054, never save and quit
with wounded health or insufficient mana. Sleep beside the healer, score after
the bounded recovery wait, and only then save and quit. Text-only room events
may recover a VNUM from an unambiguous known exit destination; ambiguous room
names must remain VNUM-less until GMCP identifies them.

Runs 8744-8746 record the latest recovery and gear-loop repair. A fed urgent
return must enter the bounded healer sleep cycle before saving; a complete
`Char.Worn` snapshot must not erase state-sensitive remove/wear/`eq all` loop
history. Run 8744 exposed the low-HP fed-return checkpoint, run 8745 was
stopped safely after the repeating gear audit and reconciled on the next start,
and run 8746 completed liquidation with 99 commands, no death, and full HP at
the healer. Preserve the guard and its regression coverage; never let a live
equipment oscillation consume the segment cap.

Runs 8726-8730 added 1,150 objective XP through source-ranked Arachnos and
Eastern Desert kills with safe healer returns. Run 8731 reached the
source-matched level-15 secretary, dealt 96 partial XP, then withdrew at the
51% calculated combat reserve and paid a 232-XP flee cost. Treat the resulting
136-XP net loss as live combat-balance evidence, not progression proof. Run
8732 completed the Plains North source circuit with the target absent and no
loss; run 8733 completed safe loot liquidation. The stale empty-packet repair
remains offline-verified and still needs a loot-bearing live reproduction.
Run 8734 completed bounded sanctuary provisioning for Aeloria and restored a
purple reserve; run 8735 completed safe liquidation without reproducing the
stale packet race. Run 8736 continued Dorrik's level-24 Mirror Realm probe and
run 8737 completed Aeloria's healer return. The source-gated finisher is
offline-verified and awaits independent live target validation.
offline-verified and awaits independent live target validation. Run 8738 added
the final safe Aeloria liquidation checkpoint at 26524 without XP change.

The latest scheduler repair preserves a registered research route's `where`
locator hazard during reconciliation, preventing an indefinitely repeated probe.
The campaign regression suite covers the registered and source-ranked cases,
and live run 8673 validated the repair safely: it recorded 150 incidental
transit XP but no objective kill before the route cap. Live runs 8658-8666
completed bounded warrior and cleric rotations safely;
Praelarran crossed level 7 and Corararfen recorded additional source-backed
early-band kills. Aeloria and Dorrik both honored current-band crowd gates.
The next proof boundary remains level 10.
Runs 8674-8676 then continued the class rotation without death or XP loss:
Praelarran recorded a 191-XP objective hermit kill and later honored a Circus
crowd, while Corararfen completed a bounded source-ranked Gnome absence probe.
These are early-band continuation records, not level-10 or HERO proof.
Runs 8677-8695 then continued the same rotation without death: Praelarran
confirmed two Circus kills for 200 objective XP and completed safe ring and
flight maintenance; Corararfen confirmed an 89-XP Circus huckster kill and
recorded a separate cult absence; Aeloria confirmed a 100-XP Moria hobgoblin
kill and a 70-XP funding orc kill, while safely recording centaur and Shadow
Keep crowd/absence outcomes. Run 8678 reached the old cleanup boundary; the
new controlled-cap path then completed runs 8679-8685 normally. These remain
continuation evidence, not level-10, subclass, or HERO proof.
Runs 8691-8696 then continued without death: Praelarran recorded a cult
absence and a crowded Circus endpoint, while Corararfen recorded a separate
Circus absence. Aeloria added another 90-XP Moria hobgoblin kill and completed
flight maintenance safely, then rejected a below-band nomad commander after a
90-XP incidental drider transit kill. These remain early-band continuation
evidence.
Runs 8699-8702 then continued Aeloria without a death: the Eastern Desert
route recorded a bounded 10-XP net loss after an incidental drider, sanctuary
recovery killed a large hobgoblin for 90 XP, and a source-matched Highland
Keeper kill added 402 objective XP and crossed her to level 18. She returned
safely to healer room 3054 with one verified purple reserve. This is executable
level-band continuation evidence, not subclass or HERO proof.
Runs 8613-8620
continued Praelarran's level-6 campaign without death or XP loss. Run 8616
directly live-validated the source-VNUM alias repair: the canonical hermit
crab stop matched DD4's shorter live `a hermit` identity, recorded 295
objective XP, and advanced the field circuit instead of looping to the runtime
cap. Runs 8614, 8619, and 8620 added clean source-ranked objective kills; the
remaining runs recorded bounded absence or maintenance. This is level-6
continuation evidence, not level-7, level-10, subclass, or HERO proof. Runs
8634-8651 then continued bounded early-band rotation. Direct run 8646
reproduced DD4's selector-only text combat-start packet ordering, preserved the
authoritative GMCP source VNUM 1524, recorded `a hermit` for 304 objective XP,
and returned Praelarran safely to healer room 3054. Campaign 11 then
reconciled the live character at 18,332 XP. Corararfen's run 8652 and Dorrik's
run 8653 also completed bounded rotations safely. This is live source-identity and
level-6 continuation evidence, not level-7, level-10, subclass, or HERO proof.
Runs 8621-8625 extended the source-identity evidence across both cleric campaigns:
Corararfen killed source mobiles 1524 and 301 for 252 and 124 XP, while Velnor
killed source mobiles 1524 and 1108 for 171 and 272 XP. Run 8622 recorded a
Shire crowd withdrawal with a net 47-XP gain and no death. These are cross-class
level-6 continuation records, not level-10, subclass, or HERO proof. Runs
8626-8628 continued Dorrik's level-24 frontier: flight was refreshed at 135
copper, source mobile 635 yielded 803 objective XP, and the following
return-home segment completed safely. There was no XP loss or death. This is
level-24 continuation evidence, not level-25, subclass, or HERO proof. Runs
8629 and 8631 completed bounded Mirror Realm research probes for Dorrik without
XP change, loss, or death. Kestrel's next invocation honored the current-reboot
fame/service cooldown without opening a duplicate live segment, and Aeloria's
latest invocation preserved her safe state while recording the Fleshmonger
crowd. These are safe frontier and cooldown records, not progression proof.
Runs
8418-8427 completed bounded autonomous
continuation: run 8418
handled optional flight maintenance; run 8419 live-considered Bardoosh and
correctly rejected its level-fuzz roll; run 8420 killed source mobile 6310, the
Bird Spider, for 369 objective XP; run 8421 recorded a zero-XP Bird Spider
result that exposed a repeatability bug; and runs 8422-8424 recorded Hood
absence, Shadow Keep crowd exhaustion, and Wyvern absence without death or
XP loss. The selector now refuses to reuse a current low-reward result even
when older source history was productive, while a separate best-reward index
allows a new level-specific policy to receive one bounded live probe. The
current source revision is
`7996722bc43508cc3773c48f8d79e3d07d68e5e4`; checkpoint 25886 is the latest
safe state. Run 8425 found source undead soldiers present in Shadow Keep but
crowded; run 8426 found the Wyvern centaur-chief absent; and run 8427 found
the Hood gang leader absent. A reset-aware continuation then returned safely
without combat or XP change. The reset-wait selector now ignores prior-level
cooldowns, so an old level-15 Ambush record cannot block or describe Aeloria's
level-17 frontier. Run 8428 then opened the bounded dynamic-wanderer research
fallback, reached source mobile 11518 in Highland room 11536, used the mage
familiar opener, and killed the Keeper of the Tower for 638 objective XP before
returning safely to the healer. Run 8429 then repeated the same bounded route,
killed the Keeper of the Tower for 477 objective XP, returned safely, and
persisted the one-shot repeatability marker. The complete offline suite passes
2,831 tests. Run 8430 then rotated to the Hood gang-leader route, recorded a
source-backed absence, and returned safely without XP change. Checkpoint 25869
was authoritative before the next rotation. Run 8431 then recorded a crowded
Shadow Keep route without combat or XP change, and run 8432 killed source
mobile 11512 in Highland room 11530 for 492 objective XP before returning
safely. Checkpoint 25877 was authoritative before the next rotation. Run 8433
completed bounded flight maintenance without XP change; run 8434 found the
Wyvern centaur-chief absent and returned safely. The bounded reset retry then
left no fresh current-band route available and checkpointed safely at 25886.
Runs 8437-8448 then continued the rotation without unsafe persistence. Runs
8444 reproduced a same-policy Mirror Realm gardener research handoff after
startup reconciliation; the selector repair now requires the next research
policy to differ from `campaign_last_policy`. Run 8445 completed Kestrel's
sanctuary recovery. Run 8446 rotated Dorrik to the source-ranked Shire Keeper
route, reached the 180-second liveness boundary, and returned him safely with
no endpoint kill, XP loss, or death. Run 8447 then rotated to the gardener
again, rejected a wandering target outside the source-safe relocation graph,
and returned safely. Run 8448 completed a fresh source-ranked Mirror Realm
probe and returned to healer room 3054 with no objective kill. The latest safe
checkpoints are Aeloria 25916, Dorrik 25936, and Kestrel 25925. This is
selector-rotation and liveness evidence, not level-18, subclass, or HERO proof.
The mage
reserve gate is candidate-specific: clean source targets can use the existing
purple reserve, while blindness-capable caster specials still require a
second purple or a trained cure. This is bounded level-17 continuation and
selector evidence with two live productive research probes, not level-18,
subclass, or HERO proof; the dynamic route remains research-status until its
promotion criteria are met. The same-reboot repeatability allowance is now
consumed and cannot reopen the route again in this reboot.
The level-aware crowd repair then ignored Dorrik's stale level-19 Eastern
Desert crowd and exposed the real level-24 Tentusks crowd. One bounded reset
retry rotated that current-band wait to an Arachnos cooldown at checkpoint
25956, with no XP loss, duplicate segment, death, or worker left behind. The
campaign suite passes 868 tests and the full offline suite passes 2,833 tests.
Run 8529 exposed a separate connection-liveness boundary while resuming
Dorrik: DD accepted TCP but sent no Telnet greeting on either bounded attempt.
The pre-login watchdog now records `login_inactivity_watchdog` and defers to
the bounded transport reconnect guard; it must never send gameplay recovery
such as `recall` before authentication. The run remained safe at checkpoint
26038 with no XP loss, death, duplicate worker, or active worker. This is
liveness evidence, not level-25, subclass, or HERO progression evidence.
Run 8530 then completed Dorrik's mirror-realm gardener research probe after DD
recovered, returning him safely to healer room 3054 at level 24 and 360,901 XP;
the 10-XP incidental increase is not objective progression. Later bounded
checks recorded the live Tentusks crowd, and one explicit reset retry rotated
to the Arachnos current-reboot cooldown at checkpoint 26065 without combat, XP
loss, or death. Velnor runs 8531-8540 added 1,250 XP, taking him from 12,175 to
13,425 XP at level 5 without a death. Corararfen reached 15,188 XP at level 6
before an honest empty-arena checkpoint, and Praelarran recorded the same
level-6 empty-arena boundary. These are continuation and reset-gate evidence,
not level-25, subclass, or HERO proof.
Velnor's runs 8544-8564 continued the source-backed early cleric rotation
without death or manual steering. He crossed from level 5 to level 6 at
checkpoint 26079 with 14,201 XP and continued through checkpoint 26101 at
14,687 XP after level-6 Mud School kills and recovery. Corararfen's run 8567 killed the
source-matched Bearded Lady for 64 objective XP and left her at checkpoint
26090 with 15,275 XP; the following cult probe was a bounded zero-XP result at
checkpoint 26092. This is live level-6 continuation evidence, not level-10,
subclass, or HERO proof.
Run 8571 then completed Dorrik's reset-aware mirror-realm gardener probe at
checkpoint 26097 without objective XP; the next selector invocation recorded
the Tentusks crowd at checkpoint 26099 and stopped before combat. Velnor's
latest safe return-home is checkpoint 26101 at 14,687 XP. These are current-band
continuation and crowd-gate records, not level-25, subclass, or HERO proof.
Runs 8574-8583 continued Velnor through the level-6 source frontier without
death; the explicit retry-stalled probe reached source mobile 4410 but honored
its below-band `consider` result, leaving checkpoint 26119 at 14,703 XP. Runs
8584-8585 gave Corararfen the same bounded Circus crowd and below-band results,
leaving checkpoint 26123 at 15,275 XP. Praelarran's runs 8586-8599 added 526
XP without death, including source-matched Bearded Lady kills for 112 and 190
XP and a Shire bull kill for 160 XP; checkpoint 26148 is alive at 15,604 XP.
The latest bounded higher-band invocations preserved Dorrik's Tentusks crowd
at checkpoint 26150, Kestrel's fame-service cooldown at checkpoint 26152, and
Aeloria's Fleshmonger crowd at checkpoint 25916. These are useful class-aware
continuation and safe-stop records, not level-25, subclass, or HERO proof.
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
Runs 8491-8494 then continued Corararfen after the level-6 transition, adding
355 net XP through seven Mud School kills and a safe healer return before an
honest empty-arena checkpoint at 26001. Runs 8495-8500 advanced Velnor through
three source-backed Mud School batches for 708 net XP; he crossed to level 5
and is alive at checkpoint 26007 in healer room 3054. These are executable
early-cleric progression records, not level-10 or HERO proof.
Runs 8501-8510 then added 579 net XP to Velnor through recovery, daycare-ring
maintenance, and six further Mud School kills. He remains level 5 at 10,789 XP
in healer room 3054 with no death or orphaned worker; the latest checkpoint is
26017. This remains early-cleric progression evidence, not level-10 or HERO
proof.
Runs 8511-8516 then added 1,074 net XP through four further Mud School
segments, a safe return-home, and daycare-ring maintenance. Velnor remains
alive at checkpoint 26023 with 11,863 XP in healer room 3054; this is still
early-cleric progression evidence, not level-10 or HERO proof.
Runs 8517-8519 then added 312 net XP to Velnor across six Mud School kills
before the arena emptied; checkpoint 26026 leaves him alive at level 5 and
12,175 XP in healer room 3054. Runs 8520-8525 added 487 net XP to Corararfen
through two further Mud School batches, recovery, and maintenance; checkpoint
26032 leaves her alive at level 6 and 15,006 XP. These remain early-cleric
progression evidence, not level-10 or HERO proof.
Run 8528 completed Corararfen's daycare-ring recovery and left her full at
checkpoint 26035 with 15,098 XP. This is a safe maintenance boundary for the
next verified level-6 segment, not level-10 or HERO proof.
Run 8394 exposed a stale-enemy cleanup edge after the source-matched Moria
large hobgoblin kill, leaving the recovered purple potion loose in inventory.
The verified `audit-combat-pouch` policy completed in run 8395 and confirmed
both pouch and reserve state before returning home. Checkpoints 25693 and
25698 preserved the crowded frontier and one automatic reset wait; no
source-safe current-band route was available under the current reboot
cooldowns. This is level-17 continuation and repair evidence, not level-18,
subclass, or HERO proof.
The source-special audit now models `spec_cast_undead` separately: it can be
selected only when the source level ceiling stays below energy drain, harm, and
gate, and a blindness-capable branch has a verified cure reserve. Aeloria's
post-audit bounded invocation preserved the existing `restock-provisions`
crowd safe-stop without opening a connection or clearing cooldown evidence.
The full offline suite passes 2,813 tests. Runs 8386-8389 then recorded a
Shadow Keep crowd, an absent centaur chief, a below-band wormkin, and a live
giant eel whose `consider` was viable. Run 8389 exposed an executor mismatch:
the source range 15-19 was rejected by an old character-level-plus-zero
ceiling. Lightning breath is now audited as a direct HP pulse, the selector
and field stop share a +2 ceiling under sanctuary and HP bounds, and startup
migration recovers the candidate from segment history because final
checkpoints omit transient source candidates. The migration clears only the
stale result, cooldown, and fastwalk sightings, retains a policy-specific
marker until a fresh segment opens, and refuses destructive breath variants.
Checkpoints 25630-25641 persisted that repair and one bounded 180-second reset
wait; the next live frontier remained blocked by Fleshmonger crowd and Hood
absence evidence, so direct eel combat revalidation remains open. Runs 8379-8380 exercised a crowded
Forest medicine-man route, immediately refreshed `where` after the target
wandered, and returned safely without XP change. Run 8381 then killed Arachnos
mobile 6317 for 708 objective XP under sanctuary; its gas breath applied DD4's
`nausea` affect with `gives: poison`, and the bot recalled after securing the
empty corpse. The repair now treats that metadata as poison in field withdrawal
and keeps a poisoned healer checkpoint asleep until the effect clears. Runs
8382-8383 completed coin banking and recovery with no death or XP loss. Run
8384 then killed the source-matched Moria large hobgoblin for 110 XP and secured
its purple potion, but a separate live source VNUM 4050 warrior remained
reported before corpse cleanup. The old guard recalled without first issuing
`consider`, costing 208 XP; the new ordering runs the post-objective consider
handler before required-loot cleanup and is covered by the exact 4055-carrier /
4050-warrior regression. Run 8385 then found the next source-ranked gang
leader absent and returned safely without another loss. Direct live re-entry
through the repaired Moria branch remains pending; these are level-17 repair
and continuation records, not level-18, subclass, or HERO proof. Run 8377
executed the source-ranked
Wyvern's Tower centaur-chief route, recorded the source target absent, and
returned safely without XP change; run 8378 completed flight maintenance. The
next invocation preserved the reboot-local absence without a duplicate run. A
non-sanctuary undead-special route needs one verified purple cure reserve;
caster specials that consume sanctuary still need two unless cure blindness is
trained. This remains level-17 continuation evidence, not HERO proof.
Run 8364 live-tested the sanctuary-aware Fleshmonger candidate: its audited
mage special blinded Aeloria, then the source `greet_prog` forced the senior
guard to attack. The runner withdrew safely for a net 179-XP loss after
consuming both purple reserves. Source parsing now captures mobile-program
triggers and hard-gates `mpkill` targets and companions before autonomous
combat. Run 8365 rotated to the registered Crystalmir white-stag probe,
confirmed the target absent, and returned Aeloria full to healer room 3054
without further XP change. These are level-17 selector and safety results,
not level-18, subclass, or HERO proof.
Runs 8366-8367 reproduced the Moria required-loot cleanup hazard. The repaired
starter permits one source-known, below-band poison pursuer after required loot
is secured, but still stops for an unmodelled pursuer; focused regression tests
cover both outcomes. Run 8372 exposed an ANSI reset before a live TARGETMODE
selector and cost 208 XP; selector matching now strips presentation bytes first.
Run 8373 then killed the source giant for 533 XP without loss. Run 8374
confirmed the selector repair and exposed an over-broad cleanup response to a
source-known below-band warrior; the final guard refinement tolerates that
bystander while retaining the unmodelled-pursuer stop. Direct live validation of
that refinement is waiting on the current restock cooldown. This remains
level-17 continuation and repair evidence, not HERO proof.
Run 8375 completed Velnor's next Mud School segment and left the cleric at
level 4, 9,502 XP, full in healer room 3054 with no death. Run 8376 stopped
Brannor before connection because no stored character credential exists; no
live character state changed. These are continuation and credential-boundary
records, not HERO proof.
Runs 8360-8363 then supplied one 787-XP giant kill, one bounded purple-reserve
return, an absent Hood probe, and flight maintenance. Run 8361 exposed a
combat-recall failure followed by an immediate duplicate recall, costing 168
net XP without death. The runner now records the failed recall and takes one
bounded flee/recovery path instead; the repair is offline-verified, while a
direct live trigger remains pending because subsequent source routes are on
current-reboot cooldown.
Runs 8340-8341 and 8348 advanced Velnor through seven verified Mud School
kills for 280, 206, and 101 XP; run 8349 then recorded the arena empty and
waited safely for its reset. Run 8351 advanced Praelarran through a wild boar
and wolf for 110 XP; run 8352 recorded the same honest empty-arena boundary.
Run 8353 completed Velnor's healer return without XP change. These are
continuation and early-class evidence, not level-10, subclass, or HERO proof.
Runs 8354-8355 exposed and repaired the Moria post-objective decision ordering
defect: a consider-only recovery route had fled from a useful-band warrior
before the exact live selector could assess it, costing 208 XP after a 110-XP
carrier kill. The post-objective consider path now precedes that generic
research-interruption guard. Run 8355 then recovered 100 XP and a second
purple reserve without loss. Run 8356 exposed the next protected-peak handoff:
the selector admitted Dwarven servant mobile 20505, but its generated field
stop still enforced a zero-level source ceiling. Protected peak stops now use
a +2 source-fuzz ceiling only when a verified sanctuary reserve halves the
source peak below maximum HP. Runs 8357-8359 completed safe Arachnos,
sanctuary-recovery, and Shadow Keep absence rotations; Aeloria ended full in
3054 at level 17 with two verified reserves. The exact live protected combat
and post-objective warrior triggers remain unobserved; this is continuation and
repair evidence, not level-18, subclass, or HERO proof.
Runs 8310-8316 live-validated the class-aware second-purple reserve gate for
Aeloria's level-17 mage frontier: an audited pouch potion counts toward the
required duplicate loot, the acquisition route requires invisibility, and the
first purple reserve is preserved while the second is acquired. Runs 8313 and
8316 then supplied 835 and 821 objective XP from source mobiles 8902 and 6367,
with no death or XP loss. Run 8328 then exposed a remaining post-objective
escape defect: DD4 charges successful flee and combat recall the same
level-scaled XP loss, and a useful-band warrior joined after a Moria carrier
kill. The runner now uses an exact live selector to consider an unknown
attacker before paying that cost and directly recalls from audited hazards.
Run 8329 live-validated the repaired ordinary Arachnos route with 566 XP and
no death or XP loss, but did not trigger the post-objective warrior branch.
Run 8334 then exposed a second-order Moria defect: repeated Char.Enemies rows
for an exact source-bound below-band required-loot carrier were counted as a
crowd, costing 208 XP without a death or objective kill. The repair permits
that duplicate packet only for exact required-loot carriers and remains
conservative for ordinary XP hunts. Runs 8331-8332 and 8335-8336 supplied one
clean 568-XP Arachnos kill plus neutral maintenance/probe segments; run 8333
was reconciled after an operator stop. Direct live revalidation of the new
repair is deferred until the current recovery cooldown clears. Aeloria is now
full in healer room 3054 with no verified combat-pouch reserve. This is
continuation and repair evidence, not level-18, subclass, or HERO proof.
Runs 8295-8296 live-validated the new level-6 source-ranked fallback: Praelarran
killed source mobile 4406 for 108 objective XP, then rotated to absent source
mobile 9851 without replaying it. Runs 8297-8299 continued the source-ranked
Circus rotation without death, run 8300 exercised the public hero
`--retry-stalled` path, and runs 8301-8302 added 103 XP from mobile 4409 and
274 XP from mobile 1138. Run 8307 exposed an endpoint identity hazard and cost
49 XP; run 8308 exposed the generic Moria locator chase and cost a further 98
XP, without a death. The recovery stop is now source-bound to mobile 4055 in
reset room 4064, and run 8309 live-validated the safe absent-carrier path with
healer sleep and no XP loss. The early fallback now records under
`source-ranked-hunt-6-10`; Praelarran is safely at 14,968 XP. Aeloria's
automatic reset retry and explicit retry-stalled retry both honored the
current-reboot Ambush cooldown rather than bypassing it. These are early-band
and safe-stop evidence, not HERO proof.
Runs 8240-8243 exposed and repaired a bounded Kestrel provisioning timeout.
Runs 8244-8249 exposed a negative-reputation Magic Shop refusal loop; the
selector now records the failed purchase and used flight loan, then stops with
`unavailable` when no independently executable non-shop frontier remains. Runs
8250-8252 live-validated the repair: Kestrel safely withdrew from the
source-verified Mirror Realm fame route at a net 111 XP loss, then reacquired
purple sanctuary and returned to healer room 3054 at level 24 and 336,913 XP.
This is selector and safety evidence, not level-25 or HERO proof.
The latest bounded Aeloria invocation ended safely while her current-band
source route waited on the reboot-local reset cooldown. Run 8253 advanced
Velnor, a human cleric, to level 4 at 6,839 XP through the verified Mud School
segment and returned him safely to healer room 3054. These are early-class and
safe-stop records, not level-10, subclass, or HERO proof.
The final-segment liveness repair is covered by 839 campaign tests and the
2,777-test offline suite. Live runs 8260-8261 completed two requested Velnor
segments, added 141 XP, and exited without the unnecessary reset wait. Run
8266 then added 267 XP through four Mud School kills; runs 8267-8269 advanced
Velnor to 8,177 XP before the reboot-local arena-empty gate. No
campaign worker remains after a completed bounded invocation.
Runs 8262-8263 gave Kestrel a source cure-critical reserve and safely rejected
the Circus fame target without combat or XP change. Dorrik's next source-ranked
probe found the Eastern Desert crowded and returned him safely. These remain
continuation and safety records, not level-25 or HERO proof.
Runs 8270-8274 continued Velnor's human cleric rotation to 8,747 XP at level 4;
the final bounded Mud School result was an honest arena-empty stop. Runs
8275-8285 continued Corararfen's independent cleric campaign through healer,
daycare-ring, and Mud School segments, adding 1,614 net XP and leaving him
alive at 9,991 XP. Both are early-class evidence and safe-stop records, not
level-10, subclass, or HERO proof. The DD4 source mirror was refreshed and was
already up to date at revision 7996722. Runs 8286-8287 then crossed Corararfen
to level 5 at 10,225 XP through another verified Mud School rotation. Runs
8288-8290 completed outfit, healer, and daycare-ring maintenance, adding 82
incidental XP and leaving him at 10,307 XP with full HP and mana in healer room
3054; no death occurred.
Run 8101 exposed an actual Kestrel death in the Circus fame-recovery route:
the ticket clerk's `built like a tank` consider warning was not yet a policy
gate, and the death reduced XP from 345,681 to 336,616 before Purgatory
recovery. The runner now rejects that warning before combat and records a
failed emergency flee so a recallable route uses recall on the next command.
Run 8102 live-validated the tank-warning rejection with no combat or death;
run 8103 reacquired the Moria sanctuary reserve for 110 XP, and run 8104
completed a safe food-reserve segment. Runs 8105-8111 then completed flight,
forest gear, funding, liquidation, and safe return-home maintenance; run 8109
added 70 XP from a source-backed John the Lumberjack funding kill. Kestrel was
at 336,796 XP before the later bounded continuation. This is safety and
level-24 continuation evidence, not
level-25, subclass, or HERO proof.
Runs 8112-8115 then recorded a bounded Kestrel fame withdrawal, crowded Moria,
an explicit stalled-candidate retry that killed the source-matched large
hobgoblin for 110 XP and recovered purple sanctuary, and an absent gnome-guard
probe. Run 8112 did not expose sanctuary expiry: the affect remained active
through combat, and the 192-XP net loss came from the health-floor withdrawal.
Runs 8116-8126 continued Velnor's human cleric through verified arena kills to
level 3; the missing Brannor credential failed fast without guessing a
password. Runs 8127-8149 created and continued Praelarran, a fresh human
warrior, through level 4; runs 8150-8223 then crossed levels 5 and 6 through
bounded arena segments, reset-aware waits, and safe healer maintenance. Run
8224 exposed the mixed below-band arena merge bug; revision 170, migration, and
regressions now preserve viable targets. Runs 8226-8228 recorded a genuine
all-below-band arena result, and run 8229 safely found the level-6 Dragon Cult
fanatic absent. These are early and level-24 continuation evidence, not
level-10, subclass, or HERO proof.
Runs 8026-8048 continued the extended Moria carrier sweep through
rooms 4064, 4063, 4058, 4057, 4062, 4065, 4066, 4069, 4071, 4072, and 4073.
The probe and hunts acquired source object VNUM 4050 and returned safely; the
ordinary campaign persisted the recovery result. Runs 8029 and 8038 produced
source-matched Dwarven Nobleman kills for 882 and 791 XP. Runs 8035 and 8043
produced source-matched Arachnos guardian kills for 622 and 705 XP. Run 8045
reproduced a late post-objective `spec_poison` escape and cost 208 XP after a
100-XP carrier kill, without a death; run 8046 preserved the reserve. Direct
run 8047 killed a carrier for 90 XP, and run 8048 found only the snake and
recalled without combat. Run 8075 then reproduced the same live poison hazard
after the carrier kill: the guard detected source mobile 4053, but a failed
recall fell through to flee and cost 774 XP without a death. The returning
branch now retries recall for an audited post-objective hazard in a recallable
room; a regression covers the failed-recall state. Runs 8076-8078 then
completed a bounded Chapel probe, a source-matched Arachnos guardian kill for
439 XP, and a Grove probe, leaving Aeloria full at 144,241 XP. The exact
pre-combat room-text rejection branch remains offline-verified but not directly
triggered in a live run. Runs 8079-8084 then completed sanctuary recovery,
Arachnos and Crystalmir rotations without loss, and runs 8085-8087 recorded
safe Arachnos, Hood, and Shadow Keep absences. Runs 8088-8089 completed an
Eastern Desert incidental drider withdrawal and safe liquidation. Run 8090
then withdrew from a Dwarven endpoint after GMCP reported two useful-band or
unknown enemies, costing 208 XP without a death; the exact policy is retained
as bounded route-risk evidence. Aeloria is now full at 145,170 XP. No HERO
claim is made.
Runs 8012-8017 completed source-backed funding, liquidation, flight,
sanctuary, and guardian rotation; run 8017 added 822 XP without death or XP
loss. Run 8018 then exposed that source mobile 4053, the `spec_poison` snake,
was already present during the required-loot Moria fight and was detected only
after combat began, costing 208 XP on recall after the potion carrier died.
The endpoint gate now resolves audited bystander specials before marking that
required-loot fight active and recalls before combat when such a hazard is
present; the late post-objective guard remains in place for hazards that appear
after combat begins. Run 8019 rotated to a crowded Dwarven Home endpoint,
skipped before combat, and returned safely with XP unchanged. This repair is
offline-verified; the extended Moria route is now directly live-validated, but
the specific room-text hazard rejection remains open. No HERO claim is made.
Runs 8005-8011 then exercised the blocked-shop funding path. Run 8006 recorded
an absent Haon Dor Shargugh; run 8007 killed source mobile 6000, John the
Lumberjack, for 60 XP and produced 80 copper-value of saleable loot; run 8008
liquidated that loot safely. Runs 8010 and 8011 recorded bounded source
absences for New Ofcol Jack and the Eastern Desert dervish. Aeloria remained
level 17 at 134,866 XP, full in healer room 3054, with no death or XP loss.
Those runs exposed that productive funding kills were not aging the blocked
flight retry counter. The runner now counts positive-XP provision funding as
productive for that cooldown, with regression coverage; the full offline suite
passes 2,765 tests. Direct live revalidation of the repaired cooldown remains
the next field task.
Run 7900 live-validated the repaired Moria locator through the ordinary
campaign selector: `where hobgoblin` reported `The maze` and `The large cave`,
the source-approved sweep found the carrier at room 4057, and Aeloria killed
it for 90 XP and acquired the exact purple sanctuary potion VNUM 4050. The
potion was stored in the combat pouch; she recalled, slept at healer room
3054, and completed without death, XP loss, or an unsafe cleanup. This proves
the repaired wandering-carrier/resource path, not level 17 or HERO progress.
Run 7907 then repeated the ordinary sanctuary-recovery policy and killed the
same source-matched carrier for 100 XP, restoring a viable purple potion
reserve. Runs 7908-7913 completed safe absence, funding, flight, guardian,
sanctuary, and elite-guard rotations; the elite guard supplied 559 XP without
death or XP loss. Runs 7914-7933 continued the current-band frontier with
bounded maintenance, source absences, Moria sanctuary-carrier kills, an elite
guard, and Bird Spider kills. Runs 7937-7945 then live-validated the inactivity
probe, Moria carrier, Dwarven Nobleman, and Bird Spider paths, adding XP without
death or XP loss; the valid checkpoint reached level 16 at 132,332 XP. These
are fresh level-16 continuation evidence, not level-17 or HERO proof.
Run 7946 did not prove completion: DD4 interleaved an immortal-arrival GMCP
snapshot for another character, Owl in Limbo, including an impossible level
106 `Char.Worth` payload. The run and segment are quarantined as failed
evidence, the raw transcript is retained, and campaign 28 resumes from its
valid healer checkpoint rather than treating the false wrapper success as HERO
progress.
Run 7948 then exposed a Moria crowd-state defect: repeated carrier records in
`Char.Enemies` were counted as material enemies even though the room's veteran
warrior and orc were source-proven below-band; the safe retreat cost 188 XP.
Run 7949 confirmed a Crystalmir absence without XP change. Run 7950 live-
validated the crowd repair: Aeloria killed the carrier for 100 XP, finished the
incidental orc for 80 XP, acquired and pouched the purple potion, and returned
safely with no retreat loss. Run 7952 then exposed a separate ordering hazard:
after the carrier kill, source mobile 4053, the sickly brown snake with
`spec_poison`, remained in combat; the pre-repair poison gate acted too late
and the segment netted only 9 XP without a death. The runner now indexes source
specials by mobile VNUM and recalls before an audited post-objective poison,
direct-damage, cleric, or mage special. Runs 7953-7955 completed flight
maintenance and two source absences safely. Aeloria is now at 132,762 XP.
These are fresh level-16 continuation and repair-evidence checkpoints, not
level-17 or HERO proof; direct live validation of the new poison boundary is
the next field task. Run 7956 then killed source mobile 6310, the Bird Spider,
for 548 objective XP and returned safely without loss. Run 7957 recorded an
absent source druidess and also returned safely. Run 7958 repeated the
source-matched Moria carrier route, killed mobile 4055 for 90 XP, acquired
the purple sanctuary potion, and returned safely. Run 7959 reached source
mobile 20504, the Dwarven Homestead nobleman, activated sanctuary, then
withdrew at the existing health floor and paid 188 XP without dying. Aeloria
is now 307 XP short of level 17. Run 7960 then killed the source-matched
large hobgoblin for 100 XP and the joining warrior for 80 XP, recovered and
pouched the purple sanctuary potion, sacrificed the emptied corpse, and
returned safely with no death or XP loss. Aeloria is now 127 XP short of level
17. Run 7961 then killed source mobile 6310, the Bird Spider, for 484 total
XP, including a critical hit and the level-up to 17. The level-up granted 8
HP, 31 mana, 10 movement, 2 physical practices, and 4 intellectual practices;
she returned full to healer room 3054 with no death or XP loss. Aeloria is now
level 17 at 133,957 XP. Run 7962 then reached the Crystalmir Lake endpoint,
issued the source-backed `where stag` search, found no White Stag, and returned
safely to healer room 3054 with XP unchanged. Run 7963 then bought and quaffed
a light blue flight potion for 30 reboot-local copper, confirmed the fly affect,
and returned full to the healer with XP unchanged. Run 7965 then killed source
mobile 4055 for 100 XP, recovered and pouched the purple sanctuary potion,
sacrificed the corpse, and returned safely. A nearby source snake and wandering
warriors were observed but not attacked; the post-objective hazard guard was
not triggered. Aeloria is level 17 at 134,057 XP with 20,393 XP to level 18.
Run 7967 then source-located Aruncus the Druid, considered him an easy kill,
used the mage familiar as the opener, and earned 169 total XP including a
critical hit. Aeloria collected the druidic staff and other drops, sacrificed
the corpse for silver, and returned full to healer room 3054. She is now level
17 at 134,178 XP with 20,272 XP to level 18. This is fresh level-17
continuation and maintenance evidence, not subclass or HERO proof. Run 7968
handled a cursed amulet safely but the live Magic Shop rejected a source
scroll even though the source prototype and shop metadata agree; keep this as
a runtime-state sale discrepancy until live object ownership is explained.
Runs 7969-7970 safely recorded a crowded Moria circuit and a below-band
secretary. Run 7971 then showed that a live level-13 ranger can outlast an
unprotected mage despite a useful consider result: Aeloria withdrew at 43/209
HP for a 48 XP net loss and returned full to healer room 3054. Quarantine that
exact Wyvern's Tower policy for the reboot; do not replay it as progression
proof. Runs 7972-7975 completed rearm, liquidation, and provision maintenance
safely. Run 7973 killed source mobile 300, Aruncus the Druid, for 246 objective
XP. Run 7976 killed source mobile 6310, the Bird Spider, safely but received
0 XP; the evidence now records `low_reward=true`, and the selector excludes
that route from productive repeats. Run 7977 rotated to source mobile 1131,
the Shire receptionist, received a negative live consider, and skipped safely.
Aeloria is now level 17 at 134,444 XP with 20,006 XP to level 18, full in
healer room 3054. Runs 7978-8002 then added bounded source absence, crowd,
identity, funding, flight, and Fewmaster Toede/giant evidence; run 7988
provided 277 objective XP and run 7997 provided 495 objective XP. Runs
7992-7993 each withdrew after a health-floor decision and paid bounded 208 XP
losses, quarantining those policies. Run 8003 reached source giant 6506 with
two live guard companions, then withdrew at 108/209 HP for 208 XP after 114
damage credit. Run 8004 reached source poison mobile 4000 at live level 10;
its aggressive room-entry attack exposed that audited specials could bypass
the below-band pre-entry gate, costing another 208 XP without death. The
selector now treats `target is aggressive` in either source hazards or legacy
rejections as a pre-entry blocker when the minimum fuzz level is below the
useful-XP floor; a focused regression covers the special case. The live state
is safely level 17 at 134,806 XP with 19,644 XP to level 18, full in healer
room 3054. The full offline suite passes 2,763 tests. Direct live validation
of the post-objective poison guard remains open.
Run 7934 then exposed a connection liveness boundary in the source-ranked
Grove route: after a valid movement command, the socket was silent for 45
seconds and the first reconnect attempt timed out. The checkpoint remained
safe, and the runner now probes an in-world socket once before reconnecting and
records bounded connect failures. Run 7937 live-validated the repaired Moria
route without a liveness timeout, killed the source carrier for 90 objective
XP, handled incidental orc XP, and returned safely. Aeloria is now at 131,149
XP; this remains level-16 continuation evidence, not HERO proof.
Run 7892 exposed a real runtime-boundary failure: a Moria sanctuary segment
ended after a snake applied poison, Aeloria fled at 1 HP, and the cleanup path
later attempted recall from POS_INCAP, which DD4 rejected. Run 7893 reconnected
to the wounded Moria body, waited through the poison death, recovered the corpse
through Purgatory, and returned safely to healer room 3054, at a cost of 3,799
XP. The repair adds an immediate recall gate for active poison, a position-aware
incapacitated wait boundary, and a runtime logout guard. Runs 7894-7898 then
completed safe Shadow Keep, elite-goblin, liquidation, return-home, and
Crystalmir continuations without another death or XP loss. The exact poisoned
Moria trigger did not recur, so ordinary post-field cleanup is live-validated;
direct re-entry through that encounter remains an explicit pending proof item.
Run 7825 promoted the source-audited noncombat Midgaard secretary into the safe
progress pool, killed source mobile 3142 for 446 objective XP, and returned
Aeloria full to healer room 3054 without a death or XP loss. This is executable
level-16 continuation evidence, not level-17 or HERO proof.
Runs 7833-7843 then exercised the source-backed 180-second reset handoff,
recorded Ambush, Shadow Keep, New Ofcol, and Haon Dor absences, and confirmed
that Moria's two large hobgoblins can wander into The maze and The large cave.
Run 7844 live-validated the level-16 mage-only deep recovery path: Aeloria
maintained bounded invisibility through the source snake room, killed the
source-matched large hobgoblin, and acquired purple sanctuary potion VNUM 4050
for 90 incidental/resource XP. Run 7845 then consumed that reserve before an
audited ranger fight and earned 445 XP without death or XP loss. Run 7848
attempted replenishment after the reserve was spent but found the carrier
absent; runs 7849-7850 likewise recorded safe no-progress absences. The
protection selector now permits a fresh level-16-and-up fixed non-combat
research probe during sanctuary cooldown, while preserving live absence,
crowd, and cleared-policy gates. Run 7853 then selected the source-ranked New
Ofcol jack at room 617, confirmed it absent, and returned Aeloria safely at
full HP and mana without XP change. Aeloria remains level 16 at 125,752 XP,
full in healer room 3054, and the reserve recovery loop remains the next live
resource gate rather than level-17 proof.
Kestrel run 7826 migrated her successful run-7128 sanctuary acquisition out of
a false below-band-consider cooldown, reacquired potion VNUM 4050 from the
large hobgoblin for 100 incidental XP, and stored one source-verified purple
potion in her combat pouch. She is safely checkpointed in healer room 3054 at
334/334 HP, 283/283 mana, and 344/380 movement. This is resource-recovery
evidence, not a current-band kill, level-25, or HERO claim.
Shared campaign SQLite uses WAL, bounded busy waiting, and immediate state-
snapshot commits; nested HERO resumes use stored manifest identity and
monotonic campaign horizons. Runs 7810-7816 completed bounded Aeloria and
Corararfen continuations without a death, orphaned run, or active bot worker;
the final Corararfen resume preserved the validation target at level 10 after a
requested target of 5. Run 7817 then completed one automatic reset retry for
Aeloria's sanctuary route without a kill or level-up and preserved the
protection marker. Campaign segment 7391 (run 7822) then selected the
independent source-ranked Midgaard secretary route during sanctuary cooldown,
earned 354 objective XP from source mobile 3142, and returned safely to healer
room 3054 without clearing the marker. Segments 7392-7393 (runs 7823-7824)
then recorded a live Haon Dor absence and a bounded Ambush no-kill result,
returning safely without XP change. Runs 7705-7713 extended the generic
level-16 rotation and
live-validated Moria sanctuary recovery after a source-aware crowd-gate repair.
Run 7709 killed the source-matched large hobgoblin for 100 XP, collected a
purple sanctuary potion, and returned Aeloria safely to healer room 3054. Run
7711 then killed source mobile 4517, the elite goblin guard, for 814 objective
XP; runs 7712-7713 completed banking and loot liquidation safely. Run
7707 remains the live crowd evidence: the room also showed a veteran warrior;
the source-aware regression classifies that descriptor by room-reachable source
VNUM only when every matching prototype is below the useful-XP floor. Runs
7714-7716 then completed healer recovery and checked Shadow Keep Wraith
prototypes 16600 and 16603, both absent, without XP change or unsafe state.
Run 7718 then killed source mobile 3142, the Midgaard secretary, for 381
objective XP; run 7719 found the Haon Dor Shargugh absent and returned safely.
Run 7721 exposed a post-objective Moria pursuer ordering defect: mobile 4051
joined after the large-hobgoblin kill and repeated flee/recall commands cost
990 XP. Run 7722 then killed source mobile 4517 for 787 objective XP and
returned safely. The repair classifies a matching live source VNUM before the
post-objective flee gate; it is covered by the full 2,718-test suite and awaits
bounded live revalidation.
Runs 7723-7725 then completed safe liquidation, return-home maintenance, and
an absent New Ofcol probe without changing XP or death state; those runs did
not reach Moria, so direct live validation of the repair remains open.
Run 7726 then killed source mobile 3142 for 286 objective XP; runs 7727-7728
checked Shadow Keep mobiles 16600 and 16603 independently and returned safely.
Runs 7729-7731 then completed safe sanctuary/Midgaard rotation without XP
change; the direct Moria repair proof remains pending. Runs 7732-7735 then
completed four bounded segments and added 593 XP without death. The interrupted
third batch was reconciled as a resumable boundary after an operator monitoring
mistake; runs 7737-7739 completed safe return-home, Ambush absence, and New
Ofcol absence checks. The live Moria VNUM repair remains pending direct
reproduction. Run 7740 then completed bounded provision restock and left
Aeloria safe at healer room 3054 with 250/300 movement. Cleric campaign 22 run
7741 added 508 XP through the generic Mud School executor and returned
Corararfen safely to healer room 3054 at level 3; this is early cross-class
evidence, not live level-11 or HERO proof.
7628-7669 extended the generic level-16 rotation and
preserved bounded absence, protection, maintenance, and safe-return evidence;
the Dwarven Homestead route remains indoors and protection-gated after a hard
health-floor withdrawal. Runs 7638, 7653, 7658, and 7665 repeatedly validated
the source-backed mage familiar opener in outdoor Ambush: Aeloria cast
`summon familiar`, grouped the pony, ordered it to attack the exact Bardoosh
instance, and then used her own combat spells for 177, 233, 191, and 191
objective XP without losing HP. This is executable level-16 continuation
evidence, not subclass or HERO proof.
For a source-verified potion keyword, the current pouch audit count is
authoritative even when an older ledger undercounted a bulk `put all` response.

When a training-priority graph changes, persist its policy revision separately
from the general campaign revision. A source-ranked segment must clear old
practice-type deferrals for one fresh trainer audit, then record the current
training revision only after the audit completes. Never let a historical
"no immediately useful listed skill" result suppress a newly registered
class-aware capability.
The public HERO workspace for Aeloria then reused her stored credential and
completed runs 7499-7513 without manual steering: the Dwarven Nobleman and
Fleshmonger routes were safely rejected, while Bardoosh mobile 4515 yielded
414 objective XP, Rock Toad mobile 2303 yielded 756 objective XP, and Aruncus
mobile 300 yielded 519 objective XP. Follow-up runs 7515-7533 continued the
same source-ranked rotation without manual steering and left Aeloria full in
healer room 3054 at 111,811 XP. This is current-band entry-point and
progression evidence, not level-16, subclass, or HERO proof. The continuation also includes
Fenanallor, a human male ranger at level 4
and 7,565 XP, safely checkpointed in healer room 3054 with primary dagger VNUM
3701 and ranged bow VNUM 3722 in distinct structured slots. Praorquilmor, a
human female brawler, reached level 3 at 4,149 XP through the Mud School arena
after the weaponless-class repair; checkpoint 23112 is also safe at healer
room 3054. These early-class checkpoints extend genericity evidence only and
are not level-10, subclass, or HERO proof. Shared SQLite writes use a
bounded 30-second busy timeout; worker segment limits remain the liveness
boundary. Kestrel run
7376 exposed a real sanctuary-expiry death at 220/334 HP
against a level-30 moose at 410/535 HP; run 7377 completed Purgatory recovery,
and run 7379 reacquired a Moria sanctuary reserve and returned full to healer
room 3054. The shared protection-loss guard now checks live player and enemy
health before another attack while preserving the near-death finisher path.
Run 7384 then killed the source-matched Midgaard secretary (mobile 3142) for
494 objective XP and returned Aeloria safely to healer room 3054. Runs
7385-7388 completed bounded healer, absence, and liquidation maintenance
without false XP. Runs 22908 and 22910 re-evaluated Dorrik's current frontier
and stopped at the Highland crowd gate without XP. Runs 7389 and 7390 then
validated explicit retry-stalled rotation: the first
reopened the fresh Mirror Realm young-boy route and recorded live absence; the
second rotated to the independent mirror guardian route, recorded a live
crowd, and returned Dorrik safely to healer room 3054 without XP change. The
SQLite checkpoints are authoritative when an outer command wrapper times out.
Run 7391 then selected Aeloria's source-ranked New Ofcol route, recorded the
target absent, and returned her safely at level 15 and 107,709 XP. Kestrel's
next bounded invocation persisted checkpoint 22941 while the fame-recovery
service remained on its current-reboot cooldown; she stayed safe in healer
room 3054 without another shop or combat attempt.
The retry-stalled repair then passed a bounded live safety check: checkpoints
22948-22954 retained Dorrik's Eastern Desert crowd result at cooldown 3 and
created no duplicate field segment or XP claim. The campaign suite passes 818
tests and the complete offline suite passes 2,678 tests. This is selector-
integrity evidence, not progression or HERO completion evidence.
Runs 7220-7229
exposed and repaired ambiguous selector-less gear identity and stale-room
ordering in the fixed rearm route; the repaired sequence validated a Queen Wasp
kill for 374 objective XP, a Giant Kodiak bear kill for 280 XP, and Aeloria's
level-15 transition. Run 7231 added 528 objective XP from Bardoosh. Runs 7230
and 7232-7235 then completed bounded level-15 and maintenance rotations safely.
Run 7236 killed Aruncus the Druid for 413 objective XP and returned safely. Runs
7237-7270 then added 5,354 objective XP from Bardoosh, Bird Spider, and Queen
Wasp kills, offset by two source-policy hard-floor withdrawals totaling 190 XP
and 20 incidental XP. Run 7283 then exposed a randomized Great Eastern Desert
DFS cycle; run 7284 recovered Aeloria through Limbo and the protected corpse
after a death that cost 3,623 XP. The repaired walker now preserves its visited
graph, the Eastern Desert route is quarantined for this reboot, and Aeloria is
12,917 XP short of level 16. Runs 7285 and 7286 then added 624 objective XP
from the Miden-nir goblin leader and Shire receptionist; the first also recorded
167 incidental XP loss after an unapproved attacker joined. Aeloria is now
12,460 XP short of level 16 and remains safely checkpointed in the healer room.
Run 7289 then killed a second source-matched Shire receptionist for 397
objective XP without an XP loss or death. Aeloria is now 12,063 XP short of
level 16. Run 7291 was a residual selector-regression invocation after the
timeout marker was cleared; it produced only 50 incidental XP from a transit
dark dwarf and no Eastern Desert objective kill. Run 7292 restored the marker
from history and selected liquidation instead, leaving that route quarantined
for this reboot. Aeloria is now 12,013 XP short of level 16. Run 7294 then
killed another source-matched Shire receptionist for 431 objective XP without an
 XP loss or death. Run 7298 added a further 368-XP receptionist kill after
addressing hunger during recovery. Aeloria is now 11,214 XP short of level 16.
Run 7301 added a further 369-XP receptionist kill and acquired a usable body
part. Aeloria is now 10,845 XP short of level 16. Run 7304 added a further
414-XP receptionist kill without an XP loss or death. Aeloria is now 10,431 XP
short of level 16. Run 7310 then added a 272-XP receptionist kill without an XP
loss or death. Aeloria is now 10,159 XP short of level 16. Run 7313 then added
333 objective XP from a receptionist without an XP loss or death; Aeloria is now
9,826 XP short of level 16. Run 7321 then added 368 objective XP from a
receptionist without an XP loss or death; Aeloria is now 8,844 XP short of level
16. Run 7324 then withdrew from an incidental fight at the hard health floor,
recording 167 XP loss, 58 net incidental XP, and no objective kill before a safe
healer return; the exact route is quarantined for rotation. Aeloria is now 8,786
XP short of level 16. Run 7328 then produced five Eastern Desert kills for 380
XP, including successful dropped-weapon recovery after a disarm; Aeloria
returned safely at 187/193 HP and was 8,406 XP short of level 16. Run 7332
added only a 50-XP dark-dwarf contact, and run 7338 repeated the 146-room Forest
absence without combat. The retry-marker guard now keeps that absent route
closed after minimum-value contact; the full offline suite passes 2,662 tests.
Run 7343 then added a clean 358-XP young dragon wormkin kill; Aeloria is now
7,998 XP short of level 16. Run 7344 then added a clean 233-XP huge python kill;
Aeloria is now 7,765 XP short of level 16. Runs 7349-7366 exercised safe
absence, provisioning, liquidation, and bounded no-progress rotation; run 7351
killed a drider for 90 objective XP and run 7367 killed a goblin leader for
another 90 XP. Aeloria is now 7,585 XP short of level 16.
Runs 7369-7372 bounded Kestrel's negative-fame recovery: the Magic Shop refused
the reboot-local flight price, a retry met a wandering-drunk route boundary,
Circus withdrew at the 39% health floor after consuming sanctuary, and Mirror
Realm recalled before combat without a sanctuary reserve. An explicit shop
refusal is a hard service boundary. Permit a non-shop fame route only with a
verified sanctuary reserve; if the remaining frontier is flight-only, return a
level-scoped `unavailable` result rather than retrying the refused shop. These
runs are research evidence, not fame-kill proof.
Run 7373 then resumed Kestrel through source food reserve route 5217, acquired
exact object VNUM 5219, returned full to healer room 3054, and logged out
without XP change, combat, or another shop attempt. Runs 7378-7379 then
completed bounded fame recovery and Moria sanctuary-reserve continuation;
run 7380 deferred the fame route as crowded without another fight. Kestrel
remains safely checkpointed in healer room 3054. Aeloria checkpoint 22859
and Dorrik checkpoint 22861 then recorded crowded current-band rooms and
deferred safely for area reset. Treat these as bounded continuation checkpoints,
not HERO completion evidence.
Source-sensitive live decisions use checkout revision 7996722. Run 7104 added
1,852 objective XP for Dorrik before the current-band frontier exhausted its
reboot-local candidates. Runs 7105-7107 recorded bounded Dorrik absences and
safe healer checkpoints. Aeloria runs 7108-7110 completed coin-stash funding,
flight purchase, and return-home maintenance; run 7112 killed Sir Durok of EAT
for 475 objective XP, and run 7113 repaired a missing ring slot. Runs 7114-7118
completed sanctuary, Shadow Keep, Old Thalos, Gremlin Lair, and Forest probes;
they returned safely, with 49 incidental XP from the later Gremlin attempt and
no additional objective kill. Run 7121 killed a source-matched Bird Spider for
600 objective XP, and run 7122 restocked safely. Run 7123 exposed a liquidation
interruption that fought a city drunk, earned 10 incidental XP, and paid a
148-XP flee cost; the utility dispatcher now flees before below-band transit
combat, with regression coverage. Run 7126 then recorded 108 incidental XP
before a shared health-floor withdrawal and safe healer return; no objective
kill was confirmed. Run 7128 killed the large hobgoblin for 90 verified XP,
recovered purple sanctuary and body-part evidence, and returned Kestrel full
after applying recovery gear. Run 7130 exposed an on-duty guard interruption on
the Fleshmonger route, costing 117 XP before a health-floor withdrawal; no death
or objective kill occurred, and the exact policy is now quarantined. Run 7133
then recorded an 83-XP loss and a 23% health-floor withdrawal on the Gizmo
route; no death or objective kill occurred, and that exact policy is now
quarantined. Run 7136 killed the source-matched huge python for 375 verified XP
and returned Aeloria full after chill-touch combat. Run 7137 killed Bardoosh for
743 verified XP, recovered a dagger after disarm, and returned full with four
drops recorded. Run 7141 killed the large hobgoblin for 321 verified XP,
recovered purple sanctuary, and returned full. Run 7142 used sanctuary, killed
the below-band Midget for 30 non-objective XP, recovered its purse and coins,
and returned full. Run 7145 killed the large hobgoblin for 283 verified XP,
recovered purple sanctuary, and returned at full health. Run 7149 killed
Bardoosh for 490 verified XP, maintained source-verified armor protection, and
returned full with three drops. Run 7155 withdrew from Bardoosh at 56% health
and cost 40 XP without a kill; it was the exact policy's second loss and is now
quarantined. The new
loss-count ledger quarantines an exact
source route after its second current-reboot XP-loss withdrawal, while a
protection recovery route on cooldown now checkpoints rather than reconnecting
without an independent alternative. Run 7156 exposed that the Forest's 80-stop
source circuit could exceed the profile's 250-command cap even when every target
was absent. The runner now derives a finite circuit allowance from registered
route and stop work, records the extension, and keeps a hard cap; Forest's
derived allowance is 613 commands. The legacy failed checkpoint reconciled to
ready, and runs 7157-7162 completed safe return-home, Shargugh, Shadow Keep,
New Ofcol, coin-funding, and flight-maintenance segments. Run 7163 killed a
source-matched Queen Wasp for 574 XP; run 7166 added 280 XP and run 7169 added
371 XP. Runs 7164-7165, 7167-7168, and 7170-7172 completed bounded absence or
maintenance routes safely. Aeloria remains full in healer room 3054. These are
continuation checkpoints, not a HERO completion claim. The earlier run ledger
is retained below as historical:
Runs 6948-6950 then completed a
bounded generic continuation: run 6949 killed the source-matched Mirror Realm
watchman for 873 XP, while runs 6948 and 6950 correctly withdrew from crowded
circuits without forcing combat. All three returned safely with no death or XP
loss; runs 6951-6960 then added 1,988 aggregate XP, including a 636-XP
Mirror Realm watchman and a 1,352-XP Kerofk route with 742 objective XP plus
610 incidental XP. Absent and crowded targets were skipped without XP loss.
Run 6963 exposed a
timed sleeping-recovery watchdog gap during flight maintenance: after one
health score, the policy suppressed its prompt gate while waiting for the
affect to expire. The starter now reopens that gate when the scheduled health
check is due; the full offline suite passes 2,636 tests, and run 6964
live-validated the repair by buying and activating flight with no XP loss.
Run 6965 completed a bounded Abyss route with the registered target absent;
run 6966 then earned 460 incidental XP from three low-risk Kerofk
interruptions, returned full to healer room 3054, and confirmed no death.
Runs 6967 and 6968 then exposed the same Abyss return hazard twice and lost
385 XP each; run 6971 live-validated the repaired return graph by skipping the
blocked recall room and returning safely when its target was absent. Runs 6974
and 6979 added 60 and 290 incidental XP without objective confirmation. Run
6981 withdrew from the level-25 fisherman at 219/542 HP for a 149-XP net loss;
run 6982 withdrew from the level-25 Donjonkeeper at 209/542 HP while it was at
157/489 HP for a 16-XP net loss. The finisher now permits one bounded final
action against a source-admitted target up to one level higher when it is at
35% health or less and the observed one-hit reserve is covered; this remains
offline-regression evidence because no matching live target has reappeared.
Run 6983 added 450 incidental XP and returned safely. Run 6987 then exposed a
different source gap: the noncombat priest of Thalos carried a held earthquake
staff, causing a 223-XP net loss before a kill. Candidate ranking now parses
source-equipped scrolls, wands, and staves and rejects an autonomous hunt when
their encoded spell behavior has not been audited. Runs 6994-7004 added
productive Moria, Mirror Realm, and Canyon evidence; run 7004 supplied 1,256
objective XP before consuming the purple sanctuary reserve. Runs 7008 and
7014 then added 886 and 799 objective XP from source-matched Mirror Realm
watchmen. Run 7013 withdrew from Dwarven Homestead at the explicit 27% health
floor after 179 incidental XP and installed a newer protection marker without
death or XP loss. The Moria recovery circuit is now one reset-room stop plus
eight bounded source-room edges, allowing a crowded room to continue to the
alternate reset without weakening the exact-one target gate. Runs 7009-7011
and 7015 completed liquidation, movement recovery, flight maintenance, and a
safe zero-kill probe. Run 7019 then live-validated the recovery circuit through
rooms 4064 and 4063, killed the source-matched carrier for 110 XP, acquired a
purple sanctuary potion, and placed it in the combat pouch before returning
full. The split circuit is now live acquisition verified; run 7022 then added
683 objective XP from the Tentusks treant and consumed that reserve, while run
7023 reacquired a purple potion through Moria and returned with 90 incidental
XP. Runs 7024-7026 recorded safe protected Mirror rotations without forcing
absent targets. Run 7027 then killed the source-matched Dwarven Home host for
1,938 objective XP and returned full to healer room 3054 with the verified
purple potion reserve intact. The full offline suite passes 2,641 tests;
Dorrik is full at 352,084 XP, 14,116 XP short of level 25. Run 7029 reacquired
the sanctuary reserve with 90 incidental XP; run 7030 safely skipped a wandering
Mirror Realm gardener outside the source-safe relocation graph. Run 7031 then
withdrew from the source-matched Solace Sergeant at Arms at the shared 30% health
floor after sanctuary expired, recording a 385-XP flee loss; run 7032 restored
full healer recovery. Run 7033 reacquired the reserve with 100 objective XP;
run 7034 safely skipped a crowded Mirror Realm target without combat. Run 7035
then killed the source-matched Dwarven Home host for 1,520 objective XP without
consuming the reserve. Run 7038 exposed a source-identity race: the expected
Grove mobile VNUM 8901 shared its live name with wandering VNUM 8900, so the
old path attacked before GMCP could disambiguate and lost 385 XP. The runner now
indexes source-graph reachability by identity and room and skips a source stop
before `consider` or `kill` whenever multiple same-name VNUMs can occupy that
room. Run 7039 restored the sanctuary reserve with 140 total XP, and run 7040
then killed the source-matched Dwarven Home host for 1,465 objective XP and
returned full to healer room 3054. Run 7041 then recorded a safe zero-kill
Mirror Realm rotation with no XP change. Run 7042 live-validated the new
pre-combat ambiguity guard at Grove room 8906: both wandering VNUMs 8900 and
8901 were source-reachable, so the runner skipped before `consider` or `kill`
with no XP loss. Run 7043 added 1,410 objective XP from the Dwarven Home host
and returned full. Run 7049 exposed a separate status-risk gap: source mobile
9202, a `spec_cast_cleric` cyclops, blinded Dorrik after sanctuary expired and
forced a flee. The run returned safely but produced a 39-XP net loss. Source
audit confirms that cleric specials can cast blindness; the runner now requires
a verified cure-blindness route before starting such a hunt, retains a second
matching potion when sanctuary would consume the first, and uses the cure
before fleeing when blindness is already active. Runs 7050 and 7051 then
completed safe sanctuary and Dwarven Home rotations without reaching that
candidate, so the repair is offline-verified but not yet live-triggered. Run
7055 then live-tested a source-matched Weeping Willow at a perfect consider:
the target drove Dorrik from full health to 137/542, the shared 35% floor fired,
and the flee cost exceeded damage credit by 213 XP. Runs 7056-7059 then
recovered and rotated through Dwarven Home, Shire, flight, and Tentusks without
another loss. Run 7060 then reopened the Dwarven Home host route: Dorrik
withdrew at 124/542 HP after earning 602 damage-credit XP, paying the 385-XP
flee cost for a 217-XP net gain without an objective kill. He returned safely
to healer room 3054 at 480/542 HP, full mana and movement, with hunger 4 and
thirst 42. Runs 7063-7066 then exercised the next protected frontier: run
7063 killed the source-matched New Ofcol teller for 1,119 objective XP with a
20-XP below-band drunk interruption; run 7064 reached the Drow weapons master
and withdrew at 43/542 HP, losing 385 XP after 23 damage-credit XP. Run 7065
replayed a Canyon `spec_cast_cleric` cyclops with the purple reserve active;
the runner quaffed sanctuary before combat, then withdrew at 80/542 HP after
the special's harm damage outlasted the aura, for a 117-XP net loss. Audited
special routes that have already failed after sanctuary are now quarantined
for the reboot rather than consuming another reserve. Run 7066 recovered the
reserve from the source-matched large hobgoblin for 100 objective XP, pouch-
stowed it, and returned full to room 3054. The full offline suite passes 2,648
tests. Runs 7081 and 7092 repeated the Drow weapons master route under its
two-mobile crowd: the first lost 210 XP, and the sanctuary-protected retry lost
265 XP at the 39% health floor. The exact route is quarantined for this reboot.
Run 7083 hit the 180-second segment boundary during a deferred Mirror Realm
search and run 7084 returned Dorrik safely; the starter now clears stale crowd
and locator waits before its runtime return boundary. Runs 7085-7091 completed
flight, New Ofcol, Moria, and bounded absence maintenance. Run 7095 then killed
the source-matched New Ofcol teller for 934 objective XP and returned full to
healer room 3054 at 358,980 XP. These are continuation
checkpoints, not a HERO claim. Objective and incidental XP
remain separate in campaign evidence. Runs 6784,
6786, 6788, 6790,
6795, 6800, and 6801 supplied productive
source-ranked kills; the latest two were the Kerofk gravedigger for 875 XP and
the Old Treant for 857 XP; run 6804 then added 891 XP from the Kerofk
gravedigger. Run 6805 completed liquidation and returned Dorrik full. Run 6807
added 784 objective XP from another Old Treant, run 6808 refreshed flight, and
run 6812 added 534 objective XP from the same route. Runs 6806, 6809, 6810,
6811, and 6813 recorded bounded zero-kill rotations. Run 6814 then withdrew
from a Shudde-M'ell interruption after the live level gate and lost 354 XP;
the exact Plains North policy was quarantined for three same-reboot segments,
and food recovery raised hunger from 5 to 40. Run 6815 then killed the
source-matched Swamp Wraith in the alternate Mahn-Tor circuit for 1,060 XP;
run 6816 restored full movement at the healer, and run 6817 recorded another
bounded Mirror Realm zero-kill result. Runs 6818 and 6827 added 726 and 637
objective XP through the generic Old Treant route. Run 6824 added 884 objective
XP from Swamp Wraith but exposed two avoidable 354-XP flee penalties from
source-known below-band Mistlings in the Mahn-Tor return maze. Runs 6785, 6787,
6789, and 6794 recorded bounded
Mirror Realm zero-kill or absence results without forcing combat; run 6793
refreshed flight, run 6796 restored hunger from 2 to 39, and runs 6797-6799
completed liquidation, safe rejection of a non-corporeal funding target, and
restock. The outer watchdog stopped the next Mirror Realm batch after it
stopped producing progress; recovery marked segment 6371 ready with explicit
interruption evidence, and run 6803 returned Dorrik safely home without XP
loss. The Mahn-Tor return policy now fights only a source-known below-band
interruption when every live enemy is below-band and health and provision gates
pass; it then resumes the live-GMCP exit graph. The focused policy set passes 38
tests and the full offline suite passes 2,629 tests. Runs 6832 and 6835 added
1,053 and 1,083 XP through the generic gravedigger route; run 6833 added 894 XP
from Old Treant, and run 6834 rejected a crowded Mirror route without XP. Dorrik
is now 9,361 XP short of level 24 and full on HP, mana, and movement in healer
room 3054. Runs 6836 and 6839 were bounded zero-XP maintenance or Mirror
rotations; run 6837 added 608 XP from Old Treant, run 6838 withdrew at the
health floor with 208 net XP, and run 6840 added 150 XP from the Arachnos
guardian. Hunger is now 2, so provision recovery is the next gate before
another field launch. Run 6841 then restored hunger to 38 while adding 716 XP
from Old Treant. Runs 6842-6845 recorded bounded Mirror, Crystal, Sentinel, and
Abyss results without forced targets; run 6846 refreshed flight. Run 6847
retained a repeated no-policy-decision watchdog failure, and run 6848
reconciled it successfully. Before run 6851, Dorrik was at 319,871 XP with
hunger 24. Run 6851 then added 687 XP from Old Treant, and
run 6852 recorded another bounded Mirror zero-kill result. Dorrik is now at
320,558 XP, 6,992 short of level 24, with hunger 24. Run 6853 recorded an
absent Highland candidate without XP; run 6854 added 646 XP from Old Treant;
and run 6855 found Nessy's child but withdrew when the adult Nessy joined,
paying the 354-XP flee cost. The exact Highland policy was quarantined and
Dorrik returned safely. He is now at 321,161 XP, 6,389 short of level 24. Run
6856 then added 1,325 XP from the source-matched Maid; run 6857 sold four items
for 291 coins; and run 6858 recorded another bounded Mirror zero-kill result.
Dorrik is now at 322,486 XP, 5,064 short of level 24. Runs 6878-6881 then
live-validated the source-route rotation repair: one empty Mirror attempt was
excluded from the next selection, flight maintenance ran, and the Old Treant
route supplied 633 objective XP before clearing the one-attempt marker. Run
6883 acquired the source-matched sanctuary potion from the large hobgoblin;
run 6887 added 760 objective XP from Old Treant. Run 6895 then withdrew from a
source-ranked Dwarven Homestead interruption at the health floor, losing 189
XP without dying and quarantining that exact route; run 6896 recorded another
bounded Mirror absence after rotation. Dorrik is now level 23 at 326,057 XP,
1,493 short of level 24, full in healer room 3054. A persisted deferred-practice
marker now prevents repeated class-trainer trips when the current trainer has
no immediately useful listed skill, while preserving legitimate reopening for
newly unlocked damage gateways. The level-20 shifter trainer has a
source-derived Kerofk locator route with bounded stale-result retries, but live
level-20 and level-30 subclass proof remain outstanding. These are continuation
checkpoints, not a HERO claim.

Latest continuation detail: runs 6897-6925 kept the source-ranked rotation
bounded; run 6921 added 802 objective XP from the Old Treant and run 6923 added
1,367 objective XP from the New Ofcol Dragonhoard teller. Run 6926 exposed a
live endpoint-gate bug when the level-19 Goblin Caves Sentry was attacked at
Dorrik's level-24 useful-XP floor despite being recorded below-band and
non-objective. The starter now withdraws before attacking such an endpoint
target, except for an explicitly source-allowed resource or required-loot
stop. Run 6927 live-validated the repair by avoiding the Sentry; runs 6928-6935
continued bounded no-objective rotations and safe healer returns. Run 6936
exposed a source-audited gas-breath special above Dorrik's live level ceiling
and caused a 385-XP flee from the level-25 Green Dragon; combat-special
admission now applies the ceiling before launch while preserving safe-noncombat
fuzz exceptions. Run 6937 completed the healer return. Run 6938 killed the
level-19 Swamp Wraith for 587 XP but encountered three source-known level-16
Mistlings during the Mahn-Tor no-recall return and paid a 385-XP flee penalty;
the return branch now keeps that bounded below-band interruption in combat.
Run 6939 refreshed flight and run 6940 added 170 XP from the Eastern Desert
worm, returning Dorrik safely to healer room 3054. Runs 6941 and 6942 then
added 933 and 1,177 XP through the Kerofk gravedigger and Old Thalos mayor,
respectively, with full healer returns and no XP loss. The full offline suite
passes 2,631 tests; Dorrik was 333,261 XP with 32,839 XP to level 25 before
runs 6948-6950. These are continuation checkpoints, not a HERO claim.

Historical pre-repair continuation anchor: Aeloria was level 14 at 88,276 XP,
Dorrik was level 22 at 290,220 XP, and Kestrel was level 24 at 363,995 XP.
Runs 6566 and 6570 added
484 and 287 objective XP to Aeloria through generic Plains North and Fleshmonger
routes. Run 6572 added 570 XP to Dorrik through the source-ranked provision
funding loop before automatic return and liquidation. The full offline suite
passes 2,614 tests. Run 6594 then proved that a foodless, nonnegative-fame
character now acquires and eats the source-matched rabbit roast before healer
recovery or funding, raising hunger from -7 to 17 and returning alive to healer
room 3054 with 481/489 HP. The current read-only DD4 source is `7996722`, and
only the expected Discord streamer remains running. Runs 6596 and 6597 then
added 560 XP to Dorrik and completed full healer recovery; run 6598 added 543
objective XP to Aeloria through the source-ranked Shire receptionist route and
returned her fully recovered to healer room 3054. This remains level-14-to-22
continuation evidence, not a HERO completion claim. Runs 6602 and 6603 then
added 450 objective XP to Dorrik and completed full healer recovery at room
3054; his current live checkpoint is 281,724 XP. Aeloria run 6616 added 221
net XP after a protected Wyvern withdrawal, and run 6617 completed a safe
Shadow Keep rotation without another XP loss. Runs 6620 through 6623 and 6628
through 6635 added 1,780 objective XP to Dorrik and left a five-pie plus
rabbit-leg food reserve in inventory, with hunger 40 at healer room 3054.
This is level-14-to-22 continuation evidence, not a HERO completion claim.
Runs 6650 and 6651 added 371 XP to Aeloria through Gremlin Lair and completed
safe recovery. Run 6658 added 330 objective XP through Plains North and run
6659 completed bounded liquidation. Run 6663 recorded a -38 XP Shire withdrawal
and run 6664 selected Shadow Keep without repeating it. Dorrik run 6653 added 280 XP through Solace;
run 6656 added 130 XP through Mirror Realm, run 6657 completed full recovery,
and run 6661 returned him safely after bounded liquidation. Run 6665 then added
130 objective XP through Mahn-Tor and left him full in healer room 3054. These are
level-14-to-22 continuation checkpoints, not a HERO completion claim. Runs
6680 through 6690 then continued the generic source-ranked rotation: bounded
gravedigger research found no target, flight and liquidation completed safely,
and Shire and Mirror Realm attempts recorded no objective kill rather than
forcing absent or unsafe targets. Run 6683 exposed stale posture after DD4
accepted wake without a position field in `Char.Vitals`; explicit sleep and
wake text now updates local state. Dorrik recovered to full resources at
285,451 XP and 352 movement in healer room 3054. The full offline suite passes
2,614 tests. These are level-22 continuation checkpoints, not a HERO completion
claim. Runs 6691 through 6698 then completed resumable maintenance and return
phases around three source-ranked probes. Mirror Realm watchman and Dwarven
routes did not prove their objective targets; one Dwarven route recorded a
reboot-local -163 XP loss and was quarantined, while incidental field kills
added 750 XP outside objective evidence. Recovery returned Dorrik full to
healer room 3054 at 285,878 XP. The next policy phase remains persisted for
later continuation. Runs 6701 through 6706 then refreshed flight and completed
bounded Abyss probes, liquidation, and healer returns without leaving a live
process behind. Run 6707 exposed that generic sanctuary recovery still used
only the short Moria reset-room stop. The repaired high-band dispatch now uses
the source-room-guided deep circuit; run 6708 acquired a purple sanctuary
potion from the large hobgoblin, recorded it in the verified combat pouch, and
returned Dorrik to healer room 3054 at 287,128 XP with full HP and mana. The
protection marker for the original failed hunt remains pending until that hunt
is retried under the new reserve. These are level-22 continuation checkpoints,
not a HERO completion claim. Runs 6709 through 6712 then exercised the
protected original hunt, incidental-loot liquidation, healer movement recovery,
and flight refresh. Run 6709 refused the crowded Ofcol teller rather than
forcing two mobiles. Run 6713 used the temporary sanctuary reserve on an
audited cleric-special cyclops route, withdrew when blindness and the live
combat state made continuation unsafe, and returned without death; the route
entered a reboot-local cooldown. Run 6714 found both Moria carriers in the
large cave and correctly refused the crowd. Run 6715 then added 653 XP through
an audited Highland alternative before an unapproved attacker joined and the
runner withdrew. Run 6716 restored Dorrik to full HP and mana in healer room
3054 at 288,592 XP. The original protection marker remains pending and the
purple reserve must be reacquired before its exact failed hunt is retried.
Runs 6717 through 6721 then completed liquidation, a productive Arikasbab
rotation, and safe healer returns; run 6718 recorded the Maid for 1,338 XP
plus two incidental rabbit kills, adding 1,628 XP and leaving Dorrik full at
290,220 XP. The next Dorrik selection correctly held on the same-reboot
sanctuary cooldown after one bounded reset retry. Aeloria runs 6722 and 6723
completed bounded Ambush and Plains North probes without objective XP; she is
safe in healer room 3054 at 174/183 HP. Kestrel run 6724 completed the
sanctuary-reserve attempt without XP, and run 6725 completed a no-kill Mirror
Realm probe; he remains full in healer room 3054 at 363,995 XP. These are
continuation checkpoints, not a HERO completion claim.

Continuation anchor for 2026-08-16: Dorrik is level 23 at 294,615 XP, full in
healer room 3054. Runs 6730, 6735, and 6737 exposed stale wandering-target,
repeated-room, and prompt-before-room ordering defects; the shared event-order
repairs now pass 2,618 offline tests. Run 6738 validated the repaired Moria
route and trainer handoff with 420 incidental XP and no false objective claim.
Run 6742 preserved a Dwarven Home health-floor withdrawal, and run 6743 killed
the level-20 gravedigger for 1,072 XP before safe healer recovery. This is
continuation evidence, not a HERO completion claim. Run 6745 then recorded a
split-locator Mirror Realm absence, four incidental kills worth 600 XP, and a
full healer return at 295,215 XP without forcing an objective claim.

Audit anchor for 2026-08-13: the live level-10 mage/thief/warrior matrix is
complete; Aeloria is level 13 at 74,825 XP, Dorrik level 16 at 123,437 XP, and
Kestrel level 24 at 360,704 XP. Run 5246 proves Dorrik's level-14 transition;
runs 5231 through 5306 prove the surrounding generic source-ranked execution
without steering, including safe healer return and preserved subclass state.
Runs 5274, 5280, 5284, and 5295 add productive current-band alternatives after
the reboot-scoped Dwarven Nobleman probe withdrew at the 15% floor without a
kill. Run 5302 then completed a successful Shire continuation. Run 5307 exposed
an armed Ambush Bardoosh critical-hit death after two incidental low-XP goblin
interruptions; Purgatory recovery, equipment restoration, and healer recovery
succeeded, leaving the durable checkpoint at 87,820 XP. Runs 5308 through
5310 then resumed with productive duty and ranger alternatives, refreshed
flight, recovered a long bow, and returned Dorrik to healer room 3054 at
88,279 XP. Runs 5311 through 5316 then completed maintenance and killed a
Shadow Wraith for 296 XP after trivial transit interruptions, returning safely
at 89,572 XP. Runs 5317 through 5319 then completed daycare and flight
maintenance and killed a source-matched ranger for 624 XP, returning safely;
the long-bow collection hit the carry-count limit without invalidating the
objective kill. Runs 5320 through 5325 then handled sanctuary and Moria
prerequisites, killed a Shire receptionist for 569 XP, and recorded both Wraith
rooms absent before returning safely. Runs 5326 through 5328 repeated the
source-backed Moria/Wraith circuit without forcing an absent objective target;
Dorrik returned safely at 91,025 XP after incidental field kills. Runs 5329
through 5334 then added ranger and Shire receptionist objective kills and
recorded the later Wraith absence without forcing combat. Runs 5335 through
5337 then completed a 743-XP Aruncus kill and safe maintenance; runs 5338 and
5339 completed two safe Wraith probes with incidental goblin XP kept separate
from objective evidence. Run 5344 then completed an Aruncus kill for 919 XP in
166.6 seconds with full health before and after; runs 5345 and 5346 found the
Wraith targets absent and retained incidental goblin XP outside objective
evidence. Run 5353 then reached the Dwarven Homestead through the Miden'nir
bridge, resolved the level-6 mountain goblin by live mobile VNUM 3501, and
recorded a positive consider result for the nobleman without attacking him.
Runs 5354 through 5358 reconciled the standalone probe's XP loss, restocked,
and rotated past crowded or absent candidates. Run 5359 then completed a
source-ranked current-band kill for 413 XP in 141.8 seconds and returned full
to healer room 3054; runs 5373, 5376, 5378, and 5383 added productive
source-matched kills, and the bounded 5385-5386 rotation crossed level 15.
Run 5391 then killed the level-15 Undead Soldier for 956 XP and returned full.
Runs 5392 through 5425 then exercised maintenance, absence, interruption,
source-special crowd, and assertive repeat branches. Run 5419 earned 286
objective XP plus 70 incidental XP and returned full. Runs 5420 and 5421 then
produced only incidental 60-XP and 10-XP transit kills while their objectives
were absent. After objective-aware progress accounting, run 5425 selected a
measured repeat and earned 303 objective XP. Runs 5426-5428 then added 1,400
aggregate XP; the productive nomad commander supplied 536 objective XP, while
the level-8 goblin leader exposed and motivated exact live below-band objective
filtering. Run 5436 then live-validated that repair: mobile 3507 loaded at
level 8, its 80-XP kill was persisted as below-band and non-objective, the
campaign recorded the exact source-policy exclusion, and Dorrik returned to
healer room 3054. Run 5437 moved on to a useful-band fanatical guard and
returned safely at 108,315 XP. Runs 5438-5443 then exercised bounded absence,
repeat, split-locator, and safe-return paths. Run 5444 live-validated immediate
split-locator resumption and safe healer logout; Dorrik is at 109,271 XP. The
following rotation exposed a cross-level status bug: measured Shire and Wyvern
repeats were allowlisted by mobile VNUM but still sorted as `fresh`, behind a
50-XP current-level repeat. Run 5460 live-validated the repair by selecting
Shire receptionist 1131, earning 401 objective XP, and returning Dorrik safely
to healer room 3054. Runs 5467 and 5468 then selected the two strongest
cross-level repeats back to back, earning 283 XP from Wyvern ranger 1706 and
317 XP from Shire receptionist 1131 before safe healer returns. Dorrik is at
111,291 XP. Runs 5470 through 5488 continued the same generic rotation while
keeping absent objectives and incidental XP separate. Run 5493 then killed
Wyvern ranger 1706 for 380 objective XP and crossed Dorrik to level 16 at
115,129 XP; the live checkpoint recorded 345 max HP, 300 max movement, three
practices, subclass `none`, and a safe healer return. Runs 5494-5496 then
proved the level-16 handoff: the
equipment audit returned safely, both Fleshmonger guards were rejected on the
prohibited below-band consider branch, the Warrior trainer accepted `shield
block` and `defense knowledge`, and Aruncus 300 yielded 519 objective XP.
Dorrik finished full at healer room 3054 with two practices and 115,688 XP.
Run 5499 then proved that required-loot accounting includes worn gear: one
worn pink ice ring left one ring outstanding, while the worn linen robe
suppressed the nanny carrier entirely. Runs 5498 and 5500 added 1,107 objective
XP from Bardoosh and Aruncus around that maintenance proof. Dorrik is now full
and safely logged out at healer room 3054 with 117,035 XP; the full offline
suite passes 2,524 tests.
Runs 5502, 5503, 5506, and 5507 then added 1,612 objective XP through
source-matched Bardoosh, Aruncus, ranger, and Bardoosh kills. Runs 5504 and
5505 interleaved bounded ring and flight maintenance without suppressing that
progress. Dorrik finished full and safely logged out at healer room 3054 with
118,647 XP, 14,953 short of level 17.
Campaign revision 164 admits a single source-proven borderline route aggressor
only when its maximum fuzzy level is exactly the useful-band fringe, it has one
global source instance, no special, fame, shop, or no-XP flag, and both its
peak-round and critical-hit bounds are below current max HP. Live GMCP remains
authoritative: defeat it only on a below-band roll; a useful-band roll follows
the existing flee-and-return path. The full offline suite passes 2,528 tests.
Run 5512 proved this gate in Ambush: three unavoidable below-band transit kills
contributed 160 incidental XP, Haglik 4519 supplied 622 objective XP, and the
below-band prisoner and elite guard were considered but not attacked. Dorrik
finished full at healer room 3054 with 119,429 XP, 14,171 short of level 17.
Run 5515 then killed Dwarven Nobleman 20504 for 963 objective XP. Run 5518
added 930 objective XP from Haglik and 160 incidental XP before returning
safely through the runtime watchdog. Dorrik is at healer room 3054 with
121,482 XP, 12,118 short of level 17.
Run 5526 live-validated mapped-room compaction: `where` reported `Path in the
plains`, the runner found Aruncus in room 302 for 501 objective XP, and returned
without a runtime boundary. Run 5527 added 655 objective Haglik XP and 160
incidental transit XP. Dorrik finished full at healer room 3054 with 123,437
XP, 10,163 short of level 17. The named-exit branch remains regression-verified
but not yet post-repair live-validated.
These are
representative checkpoints, not a HERO completion claim. Since that anchor,
runs 5856-5883 crossed Dorrik to level 19 and added a source-ranked XP-loss
ledger, safe level-19 Mirror Realm and Shadow Keep kills, an Ambush guard kill,
and a measured Eastern Desert hidden-attacker throughput result. Runs
5884-5898 then added hard-health withdrawal and sanctuary-recovery evidence,
plus a second successful worm route; Dorrik is now at 182,530 XP and safely
full in healer room 3054. Runs 5899-5918 then widened the source-ranked
level-19 rotation, including a 996-XP Dwarven giant kill, a 692-XP Solace
Foreign Trade Representative kill, and bounded empty or incident-only routes;
Dorrik is now at 184,290 XP and safely full in healer room 3054. Runs
5919-5933 then added exact Eastern Desert route quarantine, separate alternate
desert handling, two productive Arachnos routes, and two productive Solace
Secretary sweeps; Dorrik is now at 189,549 XP and safely full in healer room
3054. Runs 5934-5973 then extended the generic level-19 rotation through
Arachnos, Solace, Haon Dor, Hood, Forest, Shadow Keep, Shire, and Arikasbab.
The exact Arachnos and Arikasbab source policies that lost XP without objective
kills were deferred for this reboot, while unrelated routes continued; Dorrik
is now at 197,009 XP and safely full in healer room 3054. Runs 5974-5996 then
closed the level-19 frontier, deferred a -119-XP Mirror route, and crossed
Dorrik to level 20 through a Dwarven giant kill. He is now at 203,423 XP with
444 max HP, 218 max mana, 340 max movement, three practices, and subclass
`none`, safely in healer room 3054; the first level-20 route is active. The
Runs 6018-6021 then validated movement-starved Great Eastern Desert recovery:
the repaired runner waited through a real movement pulse, recalled from legal
room 5006 without flight, and recovered Dorrik to 444/444 HP, 218/218 mana,
and 340/340 movement before saving and quitting in healer room 3054. The
Runs 6022-6025 then resumed the level-20 rotation: after loot liquidation and
flight maintenance, run 6025 reached Solace room 10295, received a live
perfect-match consider, killed the source-matched level-19 Secretary for 888
XP, and returned safely from 176 HP to full healer recovery. Dorrik is now at
211,328 XP, safely logged out in healer room 3054. The
Runs 6026-6027 then kept the same generic rotation honest: the Solace
sergeant locator returned a live below-band no-match and was skipped, while
the Great Eastern Desert route killed the level-17 giant purple sand worm for
665 XP. Dorrik is now at 211,993 XP after another full healer recovery and
safe logout.
Runs 6028-6030 then liquidated loot, refreshed the safe healer checkpoint, and
repeated the Solace lieutenant route successfully for another 718 XP. Dorrik
is now at 212,711 XP after full healer recovery and clean logout.
Runs 6031-6032 then exercised the Shadow Keep absence gate and a live level-18
Mirror Realm watchman engagement. The watchman reached 26 HP, but critical
pound attacks and bleeding forced a flee at 50/444 HP; the net result was a
safe 193-XP gain after damage credit and the flee loss. Run 6033 killed the
level-17 giant purple sand worm for 616 objective XP; runs 6034-6035 completed
loot and return-home maintenance; run 6036 killed the source-matched level-19
Secretary on the Solace lieutenant route for 622 objective XP. Dorrik is now
at 214,142 XP, full and safely logged out in healer room 3054. These remain
representative level-20 checkpoints, not a HERO completion claim.
Runs 6037-6040 then maintained flight and funding while continuing the generic
rotation. Run 6037 recorded the live Magic Shop stock, bought a light blue
potion for 30 copper, confirmed flight, and returned to the healer. Run 6038
killed the Great Eastern Desert nomad leader for 738 objective XP; run 6039
sold its long curved sabre for 68 coins; run 6040 killed the level-17 giant
purple sand worm for 653 objective XP. Dorrik is now at 215,533 XP, full and
based in healer room 3054. These remain representative level-20 checkpoints,
not a HERO completion claim.
Runs 6041-6045 then completed worm loot and return-home maintenance and
exhausted the absent nomad circuit without forcing a target. Run 6046
live-validated the source-ranked XP-loss guard: the worm route withdrew for a
270-XP loss without an objective kill, and the exact level-20 policy was
deferred for this reboot. Run 6047 then exhausted the Shadow Keep undead
circuit with no target, while run 6048 selected an unrelated eligible Solace
Secretary and supplied 733 objective XP. Dorrik is now at 216,794 XP, full and
safely logged out in healer room 3054. These remain representative level-20
checkpoints, not a HERO completion claim.
Run 6049 then exposed a live flee-latency hazard: Dorrik reached 41/444 HP,
issued the shared 17-percent withdrawal decision, and took one already queued
combat round to 6/444 before escaping after several DD4 flee failures. He
survived, recovered at the healer, and finished at 216,813 XP. The executor now
tracks the largest target-scoped HP loss between authoritative combat snapshots
and adds one observed round to the greater of that loss or the source critical
reserve before selecting flee. This is a timing reserve, not a blanket risk
ban; reset it when the target or combat ends and validate it against live
transcripts.
Runs 6050-6051 then recovered the interrupted flight-maintenance segment and
validated a safe no-target route completion. Runs 6053-6054 exercised two live
Mirror Realm circuits: one exposed a missing destination-guided GMCP exit and
the other reached a viable young boy that departed after repeated kick attacks,
with only 16 HP lost. Run 6055 reached Moria, correctly separated two
below-band transit kills and 360 incidental XP from the below-band troll
objective, and returned full. Runs 6056-6059 then collected source-backed
coins, bought pies and water, repaired food recognition, liquidated a quoted
scroll safely, and restored the healer checkpoint. Run 6060 recorded a clean
Crystal target absence; run 6061 rejected a five-mobile Dwarven Home crowd;
run 6062 then completed two source-matched level-20 woman kills for 1,800
objective XP, bringing Dorrik to 218,973 XP at full healer recovery. These are
productive level-20 checkpoints, not a HERO completion claim.
current detailed assessment and definition of done live in
`docs/PROGRESS_AUDIT_2026-08-13.md`; the prior audit is historical.

The master product boundary is one character-independent autonomy engine that
can create any source-legal race/class/subclass request and progress it to level
100 without manual gameplay. Sex is cosmetic in DD4: accept and preserve it for
identity, but do not multiply progression coverage across sex choices. Never
add character-name-specific behavior to satisfy a live run.

The default `hero` command is the resumable to-HERO path: do not give it an
implicit outer segment cap that disables reset retries. Use an explicit
`--max-segment-runtime` only for bounded live probes or research. Each default
StarterBot segment remains bounded by the profile runtime, while the campaign
runner may continue across reboot-scoped empty-area checkpoints.

Never modify the Dragons Domain IV core repository from this project.
Treat its public source and area files as valid read-only evidence for routes,
resets, mob flags and levels, drops, shops, prerequisites, and mechanics.
Treat VNUMs as separate namespaces: room, mobile, object, and object-set VNUMs
are unique within their category, but the same number may appear across them.
Treat explicit DD4 responses confirming sleep, wake, or standing as authoritative
posture evidence when a command is accepted but `Char.Vitals` omits a position
update. Emit and persist that text-backed posture event, and never reissue
`stand` solely because a stale local position still says sleeping.
When plain combat text arrives before `Char.Enemies`, wait one bounded prompt
for the authoritative GMCP enemy record. Resolve a live enemy's source level
by its `isnpc` mobile VNUM before matching its abbreviated display name; only
then may a source-proven below-band transit attacker pass the incidental
combat gate. An unresolved attacker remains a hard route interruption.
Before any source-ranked attack, use the source wandering graph to index
same-name mobile VNUMs that can reach the current room. If the expected VNUM is
absent or another same-name VNUM is reachable, record live presence but skip
the stop before `consider` or `kill`; do not wait for post-combat GMCP to
reveal the mismatch. This pre-combat ambiguity guard is generic and never
name-specific.
Refresh `runs/dd4-source` with `git pull --ff-only` before source-sensitive
research and record the revision used for the decision. The current live
checkout used for the 2026-08-17 continuation is
`7996722bc43508cc3773c48f8d79e3d07d68e5e4`; the 2026-08-13 audit used
`f2491fd`. The bundled prerequisite and training
snapshots are pinned evidence from `f703daa`, while the fallback character
catalog is pinned to `0482387`; do not silently present a pinned snapshot as
the current checkout. If a relevant source file changes, either regenerate the
snapshot or record both revisions and re-audit the affected policy.

The registered policy table is a declarative research graph, not a live proof
ledger. After a bounded registered probe has a reboot-scoped result, the
campaign may select the generic source-ranked executor when its candidate
passes source, route, crowd, consider, health, resource, and return gates.
Use campaign segments, objective-kill records, and checkpoints to claim live
progression; `show-policy-coverage` alone never proves that a band is solved.
Treat explicit DD4 flee or death XP-loss text as authoritative negative
progress. Persist the loss evidence and accept the following GMCP progress
snapshot as authoritative; only an unexplained same-level GMCP regression
after a text score is stale. Never restore an older higher same-level XP total
merely because the regression did not include a death; the campaign must
optimize real XP per hour, including the cost of failed engagements.
Scope reboot-local source hunt kill caps by mobile prototype VNUM, not by the
mobile's display name: distinct mobile VNUMs can share a short description
(for example, two different `Secretary` prototypes). Derive source-ranked kill
counts from the selected candidate recorded in campaign segments; retain the
name-based counter only for legacy generic policies.
Do not treat an object prototype's trailing numeric level as the live level of
ordinary field loot. Follow `db.c` reset order: `G`, `E`, and ordinary `O`
loads derive from the active preceding mobile reset with mobile and object
fuzz; `P` inherits the loaded container level, `I` uses its explicit level, and
low-level Mud School mobile loot is forced to level one. Keep the prototype
value and reset-derived load range separately, and confirm consequential wear
or sale decisions with live `identify` evidence when available.
For randomized mazes, use live GMCP exit destination room VNUMs to follow a
source-backed room path; never assume the area-file direction labels remain
stable after reset.
Before selecting a source-ranked target whose route crosses a randomized room
set, preflight source-graph reachability after excluding source-proven
aggressive or special-procedure hazard rooms. Skip a candidate whose only
source-connected path is blocked; do not spend a live connection discovering
that the maze cannot reach its target.
The Great Eastern Desert pyramid maze also needs a live movement reserve:
when a no-combat return or outbound search has fewer than 12 movement points,
sleep until one live step is affordable before issuing another maze move. DD4
regenerates movement on a randomized 3.75-to-11.25 second character-update
window, so the decision must carry a 12-second asynchronous wait after the
specific recovery sleep; repeated sleep commands while already asleep are
intentional until GMCP reports enough movement. Room 5006 is the legal
underground-lake return boundary; if flight or levitation is inactive, both
generic return-home and fastwalk recovery must recall there before any fixed
route can issue the impossible west step. Never let a movement-starved maze
branch spin on repeated navigation.
The Shadow Grove (rooms 1300-1309) is a randomized `no_recall` maze. For
return-home and fastwalk recovery, navigate by live GMCP exits to room 1300,
then follow the source-backed reverse route through Haon Dor rooms 6137,
6136, 6135, 6129, 6128, 6126, 6127, 6112, 6111, 6110, 6109, 6108, 6103,
6102, 6101, 6100, 6004, 6003, 6002, 6001, 6000, and Midgaard 3052, 3040,
3012, 3013, 3014, 3005, 3001, 3054. Never rely on `recall` from a Shadow
Grove room. Live run 2623 reached and exited the grove's Galaxy approach
without invalid movement; direct recovery run 2620 also returned Kestrel to
healer room 3054.
Every Abyss room 7500-7559 is an air sector. Source rooms 7505, 7536-7539,
7548, 7551-7552, 7554-7555, and 7557-7558 are no-mob rooms that permit recall;
many surrounding rooms are `no_recall`. Use the source distance-to-recall map
and live GMCP destination VNUMs to move toward the nearest one, then recall.
Enter an Abyss route only with full movement and at least 16 visible flight
ticks, and withdraw at the 36-movement reserve. Never sleep in the Abyss:
recover the six points needed for the next flying step while standing. If
flight is already gone, do not issue impossible air movement; observe forced
falls and recall immediately upon reaching any legal room. Live run 4338
stopped Kestrel at 5 movement in room 7531, one live west step from recallable
7536. Recovery run 4339 let flight expire while sleeping, encountered mobile
7504, died after combat-locked navigation and recall retries, then traversed
Purgatory, looted the corpse in room 427, entered the portal, and reached
healer room 3054. Verification run 4340 restored and audited the equipment,
saved, and quit at full health. Live run 4352 then proved the repaired field
gate: the randomized search reached 35 movement, followed one live-GMCP step
to a source-confirmed recall room, recalled, and recovered at healer room 3054
without sleeping or fighting in the Abyss. Never let generic recall or gear handling
override active combat, Purgatory recovery, or an Abyss no-recall return.
The Purgatory portal emits the Midgaard text room and prompt before the complete
GMCP room update. Clear persisted death state when that prompt first changes the
area from Purgatory to Midgaard; otherwise a fully recovered character remains
falsely dead and the campaign fails after safe healer cleanup. Run 4564 exposed
this ordering after Kestrel looted the corpse, entered the portal, restored gear,
and recovered fully in room 3054.
The Mahn-Tor swamp (rooms 2332-2338) is another randomized `no_recall` maze.
On a return-home or runtime-watchdog boundary, follow live GMCP exits to the
stable source entrance 2331, then use the source-backed reverse route through
room 2300 to Midgaard recall room 3001 before taking the ordinary north healer
route. A fixed return-route list ending at a normal Midgaard waypoint must hand
off to the ordinary healer routes rather than report a failed maze escape.
Never retry `recall` in these rooms after DD4 answers `God has forsaken you`;
use the bounded live maze state machine and fail explicitly if its registered
exit graph is exhausted.
During that return, a live source-known below-band Mistling may be fought rather
than fled from, but only when every enemy in the room is below-band, the
character is above the normal field-combat health floor, and hunger and thirst
are not urgent. This exception is restricted to the registered Mahn-Tor return
rooms and is followed by the same live-GMCP exit graph; all other route
interruptions retain the normal flee-and-return gate. The offline regression is
verified; a fresh post-repair live trigger is still required before promotion.
Before training or automating a skill, read both its current in-game help and
its source implementation. Record whether it is active or passive, its legal
position and target, pulse/mana cost, effect formula, prerequisites, and any
equipment or status constraints; never infer behavior from the skill name.
Mirror source `do_stun` exactly for classes whose prerequisite graph exposes
it, currently base Warrior and Bounty Hunter: stun is a pre-combat action that
requires a pounding, blasting, or crushing weapon and cannot be issued after
combat begins. When a character knows both `stun` and `backstab`, retain the
best legal weapon for each action, wield the pounding weapon for the stun
attempt, then switch to the piercing weapon before backstab. Do not assume
`stun` is available to classes whose prerequisite graph does not expose it.
For a thief, the primary wield slot must hold a source-matched piercing weapon
whenever backstab is available; preserve it through sale, vault, and capacity
maintenance, recovery stance, and pre-level stance, and persist the audited
`[weapon]` slot separately from the full worn-equipment list. For a Warrior or
active Bounty Hunter, acquire and retain a separate source-matched blunt weapon
before training or relying on stun. The
opener is
`wield <pounding>`, `stun <exact target>`, `wield <piercing>`, then
`backstab <exact target>`; restore the piercing weapon before ordinary combat
or logout.
Classes whose source profile exposes `unarmed-combat` or `natural-combat`
(currently Brawler and Shifter) do not require a primary wielded weapon for
ordinary progression. An empty `wield` slot is valid for those classes; the
campaign must not send them to the weapon shop merely because the shared
equipment snapshot reports `campaign_has_weapon=false`.
For classes whose source graph exposes `disarm`, build its exact prerequisites
after the profile's earlier damage gates. Value `grip` as passive resistance
where available. Once learned and wielding a weapon, attempt `disarm` early
against each exact opponent, alternate failed retries with recurring damage
actions, and stop after success or live confirmation that the target is
unarmed. If the dropped weapon is absent when the bounded `get` recovery is
rejected, mark the weapon lost, flee immediately, and return to the healer;
never continue the field fight unarmed while the campaign rearm policy is
available.
For base Thief, include the source third-attack chain in the early damage plan:
`second attack` and `armed combat knowledge` must each reach 60 before `third
attack` unlocks. Buy a functional third attack after backstab and knife toss,
then improve second attack before third attack because `multi_hit` attempts the
third hit only after the second hit succeeds. Do not let a prior same-level
physical-practice marker suppress an entirely missing automatic attack skill.
Run class-aware training before every protected fame-recovery fight; a bounded
high-level kill must not bypass newly available damage or mitigation training.
Maintain a source-backed leveling-value analysis for every base class and
level-30 subclass, not only active test characters. Apply subclass priorities
only after live state confirms the character has subclassed. At exactly level
30, use the source short `who_name` keyword with `change` at the Kerofk class
teacher, then wait for live `Char.Base` subclass state before checkpointing or
activating subclass policies; never treat success text alone as confirmation.
Practice order
must account for prerequisite
gateways, current trainer listings and caps, separate physical/intellectual
budgets, direct damage, mitigation, sustain, mobility, and whether the combat
runner can actually use the result. Mark unsupported rotations analysis-only
rather than spending practices on unusable skills.
Persist a trainer's `no immediately useful listed skill` result by practice
type for the current character level so later field segments do not repeat the
same long trainer journey. Re-evaluate both practice types after a level gain.
Keep representative characters from different base classes in active rotation.
Use their live evidence to improve shared class-aware policy, and never let
progress on one character become a name-specific substitute for generic
race/class support.
Use explicit equipment stances. Combat gear ranks positive damroll first, then
hitroll, swiftness, and critical chance. Recovery gear favors hit points for
martial classes and mana for spellcasters; derive hybrid priorities from the
class profile. For weapons, rank estimated per-hit damage from source dice plus
damroll so a minor modifier cannot outrank a materially stronger weapon; retain
the damroll, hitroll, swiftness, then critical order for non-weapon slots.
Parse `#OBJECT_SETS` from the area files and score a complete equipment
loadout, not each slot in isolation. Mirror `handler.c`: set progress counts
distinct equipped object prototype VNUMs, duplicate copies count once, and
effects are paired with cumulative bonus thresholds in reverse area-file `A`
order. Include strength-derived hitroll and damroll changes from `str_app` when
choosing combat gear so a nominal hitroll upgrade cannot break a stronger set
bonus.
Live run 4477 validated this with Kestrel: the planner retained object 108 and
both object-6601 rings, replaced only the recovery boots with object 28372, and
finished at 5 damroll and 10 hitroll instead of the old set-breaking 3 damroll
and 11 hitroll field stance.
Treat DD4 `Char.Worn` as the authoritative worn-equipment snapshot. Resolve a
structured object VNUM before matching display text because distinct
prototypes can share a short description (for example, purchased dagger 3020
and unrelated dagger 31015). A textual `eq all` confirmation may establish
profession-visible slots, but it must not overwrite a current structured paper
doll. Mark structured identity stale when issuing a wear, remove, wield, or
hold command and restore it only from the next complete `Char.Worn` snapshot;
fall back to text only when that structured acknowledgement is absent. DD4
marks bows as a separate ranged slot even though their object prototypes are
wieldable; classify `ITEM_BOW` as `ranged_weapon` and never let a bow replace
the authoritative primary weapon. If a
complete snapshot loses the wield slot
during combat, recover the previously audited source keyword from the room and
re-wield it before recurring attacks resume. Treat `You must wield a weapon to
disarm.` as secondary evidence of the same loss. Equipment stance application
must converge. Preserve `Char.Items` target selectors and `Char.Worn`
`instance_id` to source-VNUM mappings for carried objects whose display names
are ambiguous; issue `wear #<instance_id>` for those objects and accept the
source VNUM only after the complete worn snapshot confirms it. Never collapse
distinct live instances back to one display keyword during a stance swap. Keep
a bounded repeated `(stance, worn VNUMs, inventory selectors, command)` guard;
if the same equipment state repeats twice, stop the swap, retain the current
legal gear, record the loop reason, and let the campaign continue rather than
consuming the 500-command run budget.
When a selector-less inventory description is ambiguous after a structured worn
item is removed, retain the disappeared item's source VNUM as a short-lived
description hint until the next inventory and worn state settles. Prefer that
hint over generic display matching; never alternate between distinct prototypes
such as dagger 3020 and dagger 31015.
Maintain an alternating gear-state history across complete `Char.Worn`
snapshots. If an A/B/A/B command and state cycle repeats, abort the swap,
retain the current legal loadout, and record the loop reason so the campaign can
continue. A full worn snapshot must not erase this cross-snapshot guard.
For multi-command shop maintenance, a generic prompt or unrelated room message
does not acknowledge the pending command. Wait independently for a completed
`list` response, an explicit purchase result, a wield acknowledgement or fresh
`Char.Worn`, and the requested equipment audit before advancing. Buy from an
ambiguous listing with its live `#target` selector, then verify the cloned
purchased object's source VNUM through the post-wield structured snapshot.
For fixed shop and rearm routes, a prompt or textual room description may still
refer to the origin while the authoritative `Room.Info` VNUM is in flight.
After each move, wait for that room VNUM before issuing the next route direction;
never advance a route from stale prompt text or apply the next direction twice.
Live run 4499 exposed the missing weapon recovery after a rolling-rock disarm.
Runs 4501-4502 then showed that display-only confirmation could mistake dagger
3020 for dagger 31015 and alternate forever between the object set and bead
necklaces. The structured worn snapshot and exact-VNUM policy close both
failure modes.
Live run 4505 then proved that below-band transit-attacker branches could
bypass the generic recovery block: a rolling rock removed dagger 3020 and the
runner issued recurring knife attacks before rearming. Route every decision to
continue combat through the shared disarm-recovery state machine, including
consider-only, trivial-attacker, utility, and runtime-boundary paths. Complete
the bounded get and wield sequence before another recurring action. The same
run acquired and equipped long slim dagger 5252, reached 5 damroll and 10
hitroll, and returned safely to healer room 3054.
Spellcasting combat plans must combine source-verified damage spells with
available damage-reduction spells rather than spending all mana on damage.
Apply character titles and descriptions only during initial identity setup;
use persisted command evidence to avoid recreating them on later logins. Store
new command evidence in the compact per-character command ledger at event-write
time; never scan and decode the global event history during live startup. A
persisted level above one is sufficient legacy evidence that creation-only
identity setup must not be replayed.
Live startup must not repeatedly scan full campaign histories or decode large
global event streams. Use bounded runtime tails of at most 1,024 segments and
256 checkpoints or event-bearing segments, cache those reads with write-time
invalidation, and maintain exact campaign totals plus historical command and
item evidence in compact write-time ledgers. A legacy ledger may be backfilled
once and marked complete; never repeat that backfill during later segments.
For characters below level 20, treat an affect's name as observable but do not
base decisions on GMCP duration or modifier details hidden by `do_affects`.
An affect remains active while listed; duration zero means less than one hour.
Treat each skill table `msg_off` string as a human-visible expiry signal, then
confirm the removal from the next affect snapshot before dependent travel.
Before source-backed research, and at least once per active working day,
fast-forward `runs/dd4-source` from upstream with `git pull --ff-only`; record
the revision used for consequential policy decisions.
Confirm dynamic behavior such as wandering, prices, and combat risk with live,
redacted transcripts before promoting it into an autonomous policy. Scope
prices, kill repetition, applicable object instance limits, and observed spawn
counts to the `DD was started at ...` reboot identity; never carry them across
reboots. Instance limiting applies only to the few objects whose source
definitions use it, not to mobiles.
Persist each observed reboot-specific shop price; once the current price is
known, do not treat a generic cash threshold as sufficient. Re-enter the
source-backed money loop until the character can afford that price and its
required travel and food reserve.
Persist GMCP hunger and thirst values in character and campaign state. When
negative fame blocks food service and hunger is zero or below, wake the
character immediately and launch the shortest source-safe direct-food policy
that provides enough fullness to end starvation. Never wait for healer HP
recovery while starving: live run 4629 showed starvation damage can exceed the
healer pulses. If the character is fed but lacks a reserve, collect the food
without eating it. Track exact object VNUM acquisition as success even when
urgent food is immediately eaten, then recall and resume fed healer recovery.
Live run 4633 proved the room-331 rabbit route and exact ground acquisition;
run 4634 consumed the roast and cleared hunger from -10 to 14; run 4635 then
recovered Kestrel to full HP, mana, and movement in healer room 3054. Live
run 4636 validated the fed reserve branch: it retained the roast, returned at
full resources, and persisted hunger 9 and thirst 46 in campaign state. Run
4637 then completed a full cure-critical reserve probe with the target absent,
returned to healer room 3054 at full resources, retained the roast, and
persisted hunger 6; an absent prerequisite carrier must not consume the food
reserve or strand the character in the field.
Parse `ITEM_MONEY` values as copper, silver, gold, and platinum and convert
them at 1, 10, 100, and 1,000 copper respectively. Include direct `O`/`I`
room coin resets as non-combat funding candidates when their source route has
no useful-band aggressive hazard; collect them by source keyword and verify
the currency delta before clearing the funding requirement. Treat nested
containers and unverified hoards as research-only until their extraction and
lock/key requirements are source-backed.
Include money objects loaded onto mobiles through `G`/`E` resets, including
money nested in source-linked containers, in the ordinary loot-value ranking.
These are combat funding opportunities, not permission to attack: retain the
mobile's level-band, special, crowd, route, and live `consider` gates, and use
the total copper-equivalent value when comparing a carrier with other targets.
Before a live area launch, parse each registered mobile's exact area-file room
description through the target recognizer; use live output to confirm presence
and dynamic reset state, not to discover static mobile display lines.
Before admitting a source mobile to an autonomous hunt, inspect every `E`
reset in its target room and resolve the object prototype. Parse encoded spell
names on held or wielded scrolls, wands, and staves; record the object and
spell as a hazard and reject the generic hunt until its source behavior has
been audited. A source-proven noncombat mobile special does not neutralize a
castable carried object, as live run 6987 demonstrated with Old Thalos mobile
5307 and staff 5302 (`earthquake`).
During outbound official fastwalk travel, inspect each fresh room response for
source-catalogued ground items required by the active hunt. Collect a matching
item before advancing the route index, then resume the same route step; never
use an unverified display noun or pick up a required item while in combat.
If a current-band source candidate is rejected only because one reset permits
two matching mobiles, it may enter research rotation: live TARGETMODE output
must prove exactly one source-matched target before consider or combat. Never
relax this exception for special procedures, aggression, companions, route
hazards, or larger reset capacities.
Keep a failed capacity probe quarantined for the current reboot. Only the
automatic retry after the bounded area-reset wait may reopen a fresh probe for
that source mobile; an explicit `--retry-stalled` request must rotate or wait
instead. The exact-one isolation, live consider, route, health, and return
gates still apply after reopening.
For a fixed capacity-two prototype with separate source reset rooms, tag each
stop with its own reset-room policy identity and permit at most two total kills
across the circuit. Retain the exact-one live TARGETMODE gate in every room;
skip a duplicate room and never infer per-room safety from the global reset
maximum.
For a wandering capacity-two prototype, do not collapse its bounded room
search to one kill merely because every stop shares one policy identity. Keep
the global two-kill source cap and the exact-one gate in each live room. Run
4758 followed two `where squire` locations, killed both New Ofcol squires for
422 XP total, and returned safely to healer room 3054.
When a current-reboot hunt withdraws with negative XP before a kill, persist
that policy as protection-recovery evidence and do not immediately reselect the
same source route. Recover or acquire the required protection first, or choose
another current-band route; a later retry is allowed only after the recovery
gate clears.
For source-ranked hunts, a negative net XP delta before an objective kill is
also durable evidence when consider outcomes are empty (for example, a live
GMCP level-band abort). Persist the exact policy, reboot identity, level, and
delta; exclude only that exact policy on the same reboot, and clear it only
after that policy records its own objective kill. Do not reject unrelated
current-band routes.
For a source-ranked hunt that loses XP without an objective kill, allow at most
one sanctuary-protected retry for the exact policy and reboot. Persist and
migrate a `loss_count` from campaign segments; after the second loss quarantine
that policy even if a sanctuary reserve is later reacquired. If protection
recovery is required while its sanctuary route is on cooldown and no
independent source-safe current-band route exists, checkpoint `ready` while
awaiting the area reset instead of reopening the same route or spinning a
connection loop.
Persist the completed campaign segment identifier as the loss event identity.
Startup reconstruction and interrupted-segment repair must replay the same
event idempotently; they may not increment `loss_count` merely because a
checkpoint or metadata repair ran again. Distinct completed loss segments still
increment the count and remain subject to the second-loss quarantine.
When repairing a loss ledger, use complete durable history for the recorded
source policies rather than trusting a bounded recent tail. Count distinct
completed loss segments per exact policy and reboot; if matching history exists,
replace an inflated legacy count with that count. If no matching history exists,
preserve the existing count rather than guessing that a route is safe.
If a same-reboot source route is proven absent and carries the retry-exhausted
marker, an exactly 50-XP objective contact elsewhere is still minimum-value
evidence and must not clear that marker. Keep the absent route closed until a
higher-value objective result, a level change, or a reboot; this prevents a
long empty wandering search from immediately returning after a token kill.
After two consecutive source-ranked segments produce no objective XP, pass the
trailing no-progress policies as hard selection exclusions. Do not reopen one
of those routes through the last-resort fresh fallback; checkpoint an explicit
unavailable frontier instead of spending another long live window on an
already exhausted route.
Retain that exclusion across the full bounded same-reboot runtime tail, not
just the last few policy IDs. A current-reboot crowd with `crowd_exhausted` is
also a hard route exclusion, not an active reset wait; only a non-exhausted
crowd with a live cooldown may hold an unavailable frontier. An executable
alternate policy must run immediately even when stale crowd metadata remains
in the checkpoint.
During active combat, track the largest HP loss for the current target between
authoritative snapshots. DD4's `do_flee` waits a violence pulse before reporting
failure or success, so use one additional observed round plus the greater of
the source critical-hit reserve and that observed loss as the withdrawal floor.
Reset the reserve when the target or combat ends; this absorbs command latency
without turning normal current-band combat into an automatic retreat.
Treat an explicit hard-health-floor withdrawal as stronger policy-specific
protection evidence even when partial combat produced a net XP gain. Sanctuary
may temporarily satisfy the gate, but retain it until that exact policy records
an objective kill; an unrelated easier kill must not clear it. Live runs 4387
and 4397 reached 19/305 and 26/320 HP against High Tower mobile 1303 while
gaining partial XP, proving that net XP alone does not make the retry safe.
An absent or cooldown-protected Moria carrier must not suppress generic
source ranking. Continue with a different current-band candidate while the
exact XP-losing route remains blocked by its protection marker.
For the Moria sanctuary required-loot hunt, a carrier located by `where` but
outside its source reset room is not an authorization to pursue. Record the
bounded attempt as a retryable failure with the normal three-segment cooldown,
then use the registered Argent, Shire, or deep-Moria alternate frontier before
reopening the carrier route.
Read `special.c` together with `db.c::load_specials` before classifying a
special mobile. DD4 adds +0, +5, +10, +15, or +20 to a mobile's XP modifier;
use that tier as a danger signal, not as permission by itself. The source
implementation makes `spec_fido`, `spec_janitor`, `spec_repairman`,
`spec_cast_adept`, `spec_cast_hooker`, and `spec_cast_orb` non-attacking for a
normal player, so a sole-special candidate may be audited under the ordinary
exact-target, isolated-room, live-`consider`, elevated-health, one-kill, and
healer-return gates. Do not blanket-reject every special, but keep
`spec_celestial_repairman` and crime-conditional `spec_bounty`,
`spec_clan_guard`, and `spec_executioner` research-gated until their movement
or player-status preconditions are proven.
Treat `spec_cast_cleric` and `spec_cast_mage` as status-risk specials: their
source spell tables include blindness, so a source-ranked hunt must have a
verified cure-blindness spell or potion before combat. If sanctuary is required
and the same potion supplies both sanctuary and cure blindness, retain two
verified copies. If blindness is active, cast the verified cure or quaff the
verified cure potion before fleeing; do not spend a blind recovery action on an
unverified display-name match.
When source route scoring finds one of those proven noncombat specials in a
large below-band transit crowd, retain the hazard in evidence but do not turn
it into an autonomy rejection. Ordinary aggressive crowds and all unclassified
specials remain route-gated.
For a live target-room crowd, resolve every matching source mobile profile and
retain ambiguous identities, including profiles with no special. Ignore a
bystander immediately only when every matching profile is nonempty and every
special is source-proven non-attacking or combat-only in transit. A sole
`spec_guard` profile may stop inflating the crowd only when the controlled
character's alignment is at least 300 and one complete crowd retry has passed
without hostility; lower alignment and ambiguous profiles stay blocked. Run
5418 proved the good-alignment Ofcol cityguard remained non-hostile throughout
the bounded wait, though Aruncus wandered away before consider.
When live room prose includes a qualifier absent from the source short
description, use `source_mobile_vnums_by_target_room` together with
`source_mobile_level_ranges_by_vnum` before treating it as a bystander. Ignore
that room identity only when every reachable source prototype is at least five
levels below the controlled character; use the same room-aware evidence for a
joining attacker. If any reachable prototype is unknown, mixed-level, or not
below-band, retain the crowd or interruption gate.
Do not let `fastwalk_objective_budget_complete` preempt this live-VNUM check.
When a matching `Char.Enemies` mobile has a source-known upper level at least
five levels below the controlled character, allow it through the ordinary
incidental-combat/return state even after the objective budget is complete;
keep the emergency-flee behavior for text-only or unresolved attackers. Run
7721 exposed this ordering boundary; the offline repair is not live-verified
until a bounded continuation reproduces the safe behavior.
After the one permitted below-band transit fight is complete, if a fresh
same-prototype low-level mobile is merely reported in a recallable room and
DD4 has not reported an exchange, use the existing healer route or recall
directly. Do not issue `flee` and pay level-scaled XP for a second fight that
has not begun. A different or actively engaging bystander remains a hard
second-interruption stop.
Source `spec_thief` returns before its theft branch while fighting and can take
at most 20% of carried coins while standing. Bound the possible loss to 250
copper-equivalent (so carried currency may be as high as 1,250 copper), with
the normal source level, route, crowd, live `consider`, and HP gates still
enforced. A `spec_thief`-only source-ranked probe may retain the ordinary +1
live-level fuzz allowance because the special does not add combat damage;
keep the separate coin-loss bound and do not extend this allowance to other
special procedures. Before selecting such a field route, bank carried coins
when the source 20% exposure exceeds 250 copper-equivalent, retaining one
gold as a working reserve; record this as maintenance rather than XP evidence.
The weak `spec_poison` and `spec_kungfu_poison` paths may
be audited as debuff-only targets only when the runner recalls and waits for
the healer while poison remains active. Bound weak `spec_guard`,
`spec_sahuagin_guard`, and `spec_bloodsucker` as one additional ordinary hit,
and `spec_cast_judge` as its source `6 * level` high-explosive ceiling. Keep
all other weak, moderate, strong, boss, breath, and caster specials blocked
unless a matching source damage/effect policy and live evidence are added.
Classify source-proven combat-only specials separately from target safety.
`spec_cast_undead` scans only for a victim already fighting its mobile and
returns otherwise, so a non-aggressive mobile with that special is safe to
cross without engagement. Its source spell table is level-gated: a target
whose conservative source ceiling is below 15 may be selected only with the
source-bounded chill/blindness damage reserve and a verified blindness cure
reserve; level 15 and above remains blocked because energy drain is possible.
The transit exception and this bounded combat exception are distinct and must
not be generalized without reading the specific source implementation.
Never select a mobile carrying `ACT_LOSE_FAME` for XP or funding. Live run 4564
proved that killing Solace mobile 10255 (Alex) cost 12 fame; DD4 then blocks
both shop service and leveling while fame is negative. Treat a reputation shop
refusal as a bounded, nonfatal return to the healer. When fame is negative,
restore a legal field weapon first and acquire a purple sanctuary reserve.
Try the level-31 Circus ticket clerk (mobile 4400, room 4402) before the
level-30 Mirror Realm buck or moose circuit. All three are single,
non-aggressive, special-free source resets. Attack exactly one isolated target
only when live `consider` returns the `laughs at you mercilessly` branch,
confirming the six-to-nine-level fame-award band; return to the healer after
each kill and repeat until live fame is nonnegative. DD4 ignores legacy mobile
hit and damage dice when `create_mobile` derives ordinary combat values from
live level. Shop `G` stock receives `ITEM_INVENTORY` and is extracted from a
dead shopkeeper, so never expect the clerk's ticket to drop. A live nonnegative
fame value clears the sticky shop-refusal marker.
An explicit refusal from the Magic Shop is a hard service boundary for the
current reboot: persist the reputation marker and do not retry that purchase.
When fame recovery is deferred, an ordinary grounded source route may continue,
but a flight-only fallback must not reopen the refused shop. Permit a non-shop
fame route only after a verified sanctuary reserve is present; otherwise keep
the candidate unavailable or acquire the reserve through its source-safe route.
In Circus room 4402, source-proven level-3 Bobby's mother and wandering
Midgaard Beastly Fido are trivial bystanders for the clerk probe. The latter is
`spec_fido` and cannot attack a normal player. Ignore those exact identities
there, but retain the crowd gate for every other mobile.
The fame routes require at least 95% health before the opener, but that is not
their combat withdrawal floor. Once sanctuary is confirmed and combat begins,
use the normal 15% field floor and live matchup logic; never flee merely because
health drops below the departure threshold.
Before another bounded fame-recovery fight, carry one source-verified
`cure critical` potion in the worn pouch as well as sanctuary. Select its
carrier by parsed potion effect, safe source route, mobile risk, and exact live
target count rather than by a fixed character or route. A reset capacity of two
is admissible only when TARGETMODE proves exactly one matching carrier in the
room. Use the healing reserve at or below 55% combat health without consuming
sanctuary during the below-band acquisition fight.
Potion display names are not provenance. Moria object 4150 and Thalos object
5210 are both `a black potion`; the first casts `cure critical`, while the
second casts `blindness` and `giant strength`. Retain parsed object value
strings, bind an ambiguous potion to the exact source reset that produced it,
persist that verified count across pouch audits, and decrement it when quaffed.
Never classify, stow, or quaff an ambiguous black potion from name alone.
Select any source-safe potion that provides the required spell, then persist
and use its actual source-unambiguous command keyword; do not pin cure-critical
acquisition to a black potion or one route. DD4's multi-object `put all.<name>`
path can place non-potions in a worn pouch, so stow one exact collision-free
selector at a time and remove any audited pouch contaminant before combat.
If sanctuary expires before a protected opener and no reserve remains, record
the target as live and viable with a sanctuary dependency. Do not assign an
absence or generic failed-hunt cooldown; acquire a new reserve first, then
return to the same gated target.
After an absent or rejected fame target, require three productive field
segments before retrying that exact circuit. Preserve the sanctuary potion
until a source-matched target passes its live consider gate; ordinary
source-ranked alternatives must not consume it. A living low-roll Mirror
Realm mobile retains its live level until it dies or the world reboots, so a
cooldown alone cannot reroll it.
The flight-assisted Lotus Temple chamber attendant (mobile 10736, room 10837)
is an independent fame-recovery research route only while carrying both a
light blue flight potion and a purple sanctuary potion. Live run 4581 reached
the level-31 attendant and exposed a post-opener guard that incorrectly
reapplied the ordinary +1 level ceiling after the six-to-nine-level consider
gate. Twenty-two failed flee attempts ended in death; the Purgatory controller
recovered the corpse and returned Kestrel fully equipped to healer room 3054.
The active-combat GMCP guard must honor the current stop's explicit maximum
level offset. Any research-hunt death is nevertheless durable fatal evidence,
including a death after the nominal target kill when the whole attempt loses
XP: preserve the objective-kill observation for audit, but do not mark the
route viable or reopen that exact policy at the same character level and
reboot, even after ordinary retry cooldowns expire.
Any explicitly audited `spec_cast_mage` hunt must mark sanctuary as required,
quaff its carried purple potion before the opener, and confirm the sanctuary
affect before attacking. Live run 4217 exposed the unsafe gap between merely
carrying a reserve and consuming it: unprotected fireball and colour spray
forced a withdrawal from the Shire dwarven prince.
If a source peak-damage rejection is caused only by the maximum fuzzy mobile
level, allow it only as an explicit reset-retry probe when the minimum source
peak is below current max HP. Require exact live `consider` level (no positive
level offset), at least 95% health, and no other source rejection; record the
probe separately and never treat its conservative maximum as ordinary combat
permission.
When the ordinary current-band frontier is exhausted, a source mobile exactly
one base level above the character may enter a separate ceiling-probe pool only
when its full fuzzy peak-round bound is strictly below current max HP, it has
no source rejection or coin-stash role, and its lower fuzzy range remains
useful. Require live `consider` to return the perfect-match branch, retain the
normal +1 live-level stop ceiling, and never generalize this exception to
special, aggressive, crowded, or route-hazard targets.
Also permit a source mobile whose nominal base level equals the character's
current level when only one additional fuzzy level exceeds the ordinary upper
band, provided it is autonomous-safe, special-free, rejection-free, single-
spawn, and its estimated peak round damage is strictly below max HP. Treat it
as the same bounded live-consider probe; do not relax the +1 live-level combat
ceiling or the normal route and crowd gates.
Live run 3613 validated this gate against the Old Treant in Mahn-Tor: Kestrel
earned 1,644 XP and returned to healer room 3054 at 236/283 HP. Live run 3618
then validated the independent Solace secretary reset for 1,198 XP without
player damage. Preserve both as reusable level-20 source-ranked evidence. Live
run 4638 killed the level-band Old Treant for 971 XP while losing only 9 HP;
that margin requires continuation to another vetted target when a safe circuit
is available instead of an unconditional single-kill recall.
When comparing an exact registered target with a parsed live identity, strip
only leading grammatical articles (`a`, `an`, `the`) on both sides; preserve
the remaining source identity and selector distinctions.
For source-backed discovery, treat fixed `ACT_SENTINEL` mobiles and
`ACT_DIE_IF_MASTER_GONE` mobiles as reset-room-only. For ordinary mobiles,
search every bounded source-reachable room from every reset, blocking
`EX_CLOSED`, `ROOM_NO_MOB`, and stay-area boundaries. An open exit is
mobile-reachable even if its lock flag remains set. `AFF_CONFUSION` is a
separate source movement path that overrides sentinel, stay-area, and no-mob
restrictions, so search its full bounded open-exit graph. If `where` confirms a
target but its room label is unmapped, retain that positive evidence and run
the full bounded source search instead of abandoning the target.
`where` may list several same-named mobiles from unrelated areas; retain every
matching row, prefer source-vetted safe locations, and never let the first row
hide a later mapped location. Treat an excluded location as fatal only when no
safe source-vetted match remains.
DD4 may send a prompt before the rows of a `where` response. A bounded locator
grace timer must be evaluated before the ordinary `prompt_ready` gate so its
expiry can wake the policy without another server prompt. Apply the same rule
to the magic-shop drunk preflight. Preserve a synthetic line boundary when a
new locator header begins in a later socket read, but do not split a target row
that genuinely continues across reads. Run 5442 exposed both defects by
waiting for the inactivity watchdog after `where nomad`. Run 5444 then parsed
the delayed leader row in Fungus Temple, issued its next command in the same
timestamped read, completed the bounded search without a watchdog event, and
saved and quit at healer room 3054.
Any intentional `None` decision during sleeping or other timed recovery must
have a persisted deadline that is evaluated before the ordinary `prompt_ready`
gate. When that deadline expires, reopen the policy gate and issue the bounded
health or state check; add a regression with `prompt_ready` false. A live
watchdog may stop a stalled segment, but it must never be the only mechanism
that can wake a timer-backed recovery state. When a bounded field segment
reaches its runtime boundary, clear pending crowd or locator response deadlines
and restore the prompt gate before dispatching return-home; stale deferred waits
must never suppress recall or cause the outer timeout to strand the character.
Normalize flattened GMCP room descriptions with the same sentence boundaries
used by live room output before applying crowd gates; furniture or other static
room prose must not become a phantom mobile. Ignore companions only when their
source identity is explicitly trivial for the current character level.
When the source mobile catalog is available, subtract static GMCP room prose
only through exact normalized source display-line matches. Never subtract a
live source-matched mobile by a generic noun parsed from differently worded
room prose. Run 4773 incorrectly removed the visible Fleshmonger cook because
the room said `a cook is bent` while the mobile said `the cook bends`; run 4779
then retained selector 23775, killed the cook for 322 XP, recovered its dropped
weapon after a disarm, and returned safely to healer room 3054.
Keep source-ranked evidence keyed by area, mobile VNUM, reset-room VNUM, and
character level. Do not let a crowd or absence result from one reset room
suppress an independent reset room for the same mobile; only a legacy,
explicitly multi-room policy may aggregate those locations.
The requested mobile's own reset rooms are valid endpoints even when that
mobile is aggressive; block other aggressive reset rooms as route hazards and
let the live crowd/isolation gate decide. A visible room target or positive
`where` row remains presence evidence even when `consider` rejects it as
below-band or too dangerous; never serialize that case as target absence.
Never attack for XP when `consider` returns a `do_consider` result from the
`diff <= -5` or `diff <= -10` branches; those targets are too low to be useful.
Apply the same floor when authoritative `Char.Enemies` identifies the exact
source target at five or more levels below the character after aggression has
already forced combat. Finish a harmless unavoidable fight when appropriate,
but record the kill as incidental, persist the exact source-policy below-band
sighting, and do not let its XP satisfy the objective or reset no-progress
selection. Explicit required-loot carriers retain their separate audited
exception. Run 5426 exposed this when level-15 Dorrik's selected goblin leader
loaded at level 8 and paid only 80 XP among forced Miden'nir attackers. Run
5436 proved the repaired path end to end: the SQLite kill ledger stores
`below_useful_band=1` and `objective_eligible=0`, omits source-policy credit,
and restart reconciliation filters the row from objective progress.
Treat an explicit objective kill below 50 XP as contact evidence only, not as
productive source history or permission to repeat a route. Use the tagged
`source_policy_id`/mobile VNUM for wandering kills; never attribute the reward
to the selected room or a display-name anchor. Fall back to the segment XP
delta only for legacy kill records that lack explicit objective XP metadata.
When the best fresh source prototype has less than a 50% chance for its normal
level fuzz to land inside the useful consider band, prefer a same-reboot route
whose latest recorded kill still earned meaningful XP, even after its third
kill. High-confidence fresh targets retain priority, and a repeat stops being
eligible when its latest reward falls below the meaningful-XP threshold.
Apply the 50% fresh threshold across the complete research pool ordering, not
only within one candidate category. A low-probability capacity probe must not
hide a high-confidence level-ceiling probe merely because capacity research is
visited first. At level 11, revision 162 replaced the 20%-useful Circus father
with the 60%-useful Shire receptionist; live run 4771 earned 743 XP and returned
safely to healer room 3054.
Carry that reward evidence across a character level boundary by source mobile
VNUM, not by the generated policy ID's level suffix. Use the tagged objective
kill's `xp_gained`, because a level transition can make the aggregate XP delta
look negligible. Campaign revision 156 threads those proven repeats through
same-area circuit construction, so capped but still-productive mobiles can
form a multi-kill route while live consider, crowd, health, and below-band
gates remain mandatory.
When a cross-level repeat is allowlisted by that evidence, classify it as
`productive` for candidate ordering even if its new level-suffixed policy ID
has no direct result yet. Do not let a weak current-level repeat outrank it
merely because the regenerated ID is marked `fresh`. Run 5460 proved this
handoff by replacing a 50-XP Ambush goblin route with the Shire receptionist
and earning 401 objective XP. Runs 5467-5468 then proved repeat rotation after
cooldown by earning another 600 objective XP from the Wyvern and Shire routes.
Run 5493 proved that the same source-mobile reward continuity survives through
the next level transition: ranger 1706 earned 380 objective XP, crossed Dorrik
to level 16, and returned him safely to healer room 3054.
If the fresh selector initially returns a research-only candidate, still
evaluate the current-band productive repeat pool before stopping or exposing
the research route. Research must never mask executable progress. For legacy
source-ranked segments that lack a mobile VNUM, carry forward XP only from the
unambiguous selected candidate record; never guess an identity from a display
name or assign the reward to a different prototype.
Live run 4727 validated the level-11 Gnome circuit after seven same-reboot
kills per prototype: Aeloria killed treasurer 1521 for 368 XP, continued to
cook 1526 for 191 XP, ate the cook's severed leg, then returned to healer room
3054 at full health and movement. Preserve the tagged reward per mobile VNUM
and the two-kill route as reusable evidence until a later reward falls below
the meaningful-XP threshold or a live gate rejects either stop.
Do not poll a just-killed source prototype before its area can plausibly reset.
Campaign revision 158 blocks each tagged mobile VNUM until two later completed
source-ranked hunt segments have run; city maintenance does not count. Live
run 4731 killed the Gnome pair for 448 XP, run 4732 supplied only one
intervening Daycare hunt, and premature run 4733 then found both Gnomes absent.
The two-segment cooldown would have blocked exactly that wasted revisit while
leaving other areas available for productive work.
Live run 4734 validated the selector boundary: it withheld the recent Gnome
and Daycare VNUMs, killed Moria large orc 4005 for 166 XP instead, and returned
to healer room 3054 at full health, mana, and movement.
Live run 5047 exposed a route-throughput hazard in the Gnome kitchen approach:
the source-safe cook route crossed barracks resets permitting up to 15-20
below-band aggressive soldiers, producing a long chain of incidental 20-40 XP
kills before the useful endpoint. Reject a route that crosses an aggressive
below-band reset with capacity greater than four, while retaining lone
source-proven below-band interruptions as finishable transit hazards. A
source-backed required-loot reserve may retain that route only when its exact
carrier also passes the one-live-target, isolation, health, and item-provenance
gates; this exception does not reopen the route for ordinary XP hunting.
Bound that discovery preference with durable throughput evidence: after two
consecutive same-level, same-reboot source-ranked segments earn zero XP, choose
a proven meaningful repeat even when the next fresh candidate has at least 50%
useful fuzz odds. Derive the streak from campaign segment history, ignore city
maintenance between hunts, and reset it on XP gain, level change, or reboot.
Runs 4537-4541 produced five consecutive zero-XP probes after run 4535 earned
1,044 XP, proving that unbounded fresh discovery can displace progression.
An explicit `--retry-stalled` rotation may reopen a current-reboot
retry-exhausted policy only when that exact policy is also a meaningful,
productive repeat. Keep the marker binding during normal selection and never
use the switch to open unrelated absence, crowd, protection, or route-hazard
cooldowns.
When a normal source-ranked segment makes no progress because its selected
route is absent, crowded, unreachable, or otherwise safely unsuccessful,
persist `campaign_source_ranked_retry_exhausted_policy` with the current boot
identity and clear the candidate before the next selection. This is a
one-attempt exclusion: a productive objective kill clears it, while the next
selection rotates to another eligible route or waits for reset. Do not let a
short absence retry cooldown replay the same empty route immediately. The
marker is scheduling evidence only; claim progression from objective-kill
records and checkpoints.
Use the source level-difference branch as the level-band decision: the separate
hitpoint comparison text is descriptive combat-risk context, not a substitute
for level difference and not an automatic rejection of an otherwise viable
level-band target.
For source-ranked hunts, persist a negative live `consider` separately from a
failed combat attempt; a short retry cooldown must not reopen a target already
reported as materially stronger than the character.
Live runs 4299 and 4325 exposed this exact failure for Hightower mobile 1303:
productive work expired its generic retry marker and reopened the same diamond
golem at level 22 in the same reboot. Preserve `consider_viable: false` as
terminal for that policy and discard its short retry cooldown instead.
Persist that below-band result against the selected policy for the current
character level and reboot. Do not revisit the same surviving mobile until the
level or reboot identity changes.
For the optional `recover-daycare-ring` equipment probe, a live below-band
source target is terminal for the current level and reboot: persist
`campaign_daycare_ring_blocked_level` and
`campaign_daycare_ring_blocked_boot_id`, clear the temporary countdown, and
reopen only after either identity changes. Do not spend productive field
segments retrying that same ring route.
Attach a below-band source-mobile key only when the active execution is the
matching source-ranked policy. Bespoke equipment or maintenance hunts may
inherit a stale candidate record at their checkpoint boundary; never let that
record exclude an unrelated source mobile. Sanitize mismatched and non-source
keys during policy revision repair.
Every shared probe-to-hunt promotion and fallback must enforce both the
policy's minimum and maximum character level. Live run 4223 proved that an
expired level-18 Rock Toad policy is below-band and wasteful at level 22; a
cooldown or protection-recovery path must not revive it outside its band. Live
run 4408 caught the Moria-absence alternate helper reviving the same fallback
at level 23, so enforce the bounds inside helper-level fallback branches too.
The next registered high-level extension is the 46-50 Dwarven Home chess-room
dwarf (mobile 20514, room 20530), followed by the Mirror Realm Storn fallback
(mobile 19034, room 19114), both source-registered from revision `bf745c3` as
sentinel/stay-area, no-special probes. Their combat policies remain research-
gated until live exact-target, crowd, and level-difference evidence promotes
them; HP thresholds govern combat withdrawal only.
The next registered extension is the 51-55 Darkwood strange mist (mobile 11200,
room 11211) followed by the Dwarven Home gambler (mobile 20515, room 20531),
also source-registered from `bf745c3` as sentinel/stay-area, no-special probes.
Bind their live lines to `strange mist` and `dwarf`; the level-difference branch
of `consider` decides XP-band eligibility, while hitpoint text only informs
combat-risk gates.
The 56-60 extension is the Dwarven Home master of the house (mobile 20517,
room 20537), source-registered from `bf745c3` as a single sentinel/stay-area,
no-special target with a source-equipped dwarven dagger. Bind its live line to
`master of the house`; require the same exact-target, single-reset,
level-difference, health, and healer-return gates before promoting a hunt.
The 61-65 extension is the Vamp Hive wounded vampire (mobile 25652, room
25641), source-registered from `bf745c3` as a single non-aggressive,
stay-area, no-special mobile with source-equipped sharp fangs, black cloth
trousers, and an elegant black cane. Use `where vampire` before the bounded
reset-room search; bind the source line to `wounded vampire` and do not expand
the wandering search space without fresh live room evidence.
The 66-70 extension is the Tabernacle hulking beast (mobile 39013, room
39016), source-registered from `bf745c3` as a single sentinel/non-aggressive,
no-special target with no source equipment or room companion. Bind its source
line to `hulking beast` and keep the exact-room, level-difference, health, and
healer-return gates before promoting combat.
Live run 2640 reached the Shire research circuit at level 18 and safely returned
to healer room 3054 with full health, but the MUD connection dropped during a
field `look`. Reconnecting placed Kestrel in Midgaard while the local cursor
still expected room 1123; `StarterPolicy.on_connection_closed()` therefore
marks any in-world field route for healer recovery, clears pending travel state,
and lets the campaign retry the segment instead of treating stale navigation as
current-room evidence.
Rerun 2642 used SQLite event freshness rather than JSONL file size as its live
watchdog: the level-18 Shire probe completed without combat, found the target
absent, returned Kestrel to healer room 3054 at full health, and checkpointed
the campaign for a later reset retry.
Treat `hide` as a stationary ambush or avoidance skill because ordinary
movement removes it; do not use it as travel concealment.
Before a mage field fastwalk, establish known invisibility at recall so
wandering Midgaard greet-program mobiles cannot replace a productive target
with a trivial forced fight. Cast it before stepping south for the fountain
water preflight, then confirm the affect before moving. Live run 4702 reached
the fountain before casting and was forced to kill the wandering drunk for 10
XP; the ordering fix prevents that avoidable transit combat.
Before a Magic Shop trip, use known invisibility when available. Otherwise
issue `where drunk` from healer room 3054 and defer the trip when mobile 3064
is in a source-route room. Its `greet_prog` calls `mpkill`, while
`mprog_greet_trigger` requires the mobile to see the entering player. Treat a
blocked route as a bounded retry after productive work, not as an
unaffordable-purchase result.
Live runs 4668-4669 exposed an immediate next-connection retry despite the
three-segment marker: run 4668 correctly stayed at the healer while the drunk
blocked the route, but run 4669 immediately crossed the now-clear route and
bought flight. Campaign policy revision 148 therefore persists the route block
against the reboot identity, suppresses another affordable purchase until
three productive field segments advance the cooldown, and clears the block
only when that cooldown completes, active flight is confirmed, or the reboot
identity changes.
For verified hunts, continue until a meaningful discomfort threshold: low
health without vetted local recovery, an uncured disabling affect, unusable
food or water when needed, insufficient movement, encumbrance, or exhausted
local targets. Prefer source-vetted local sleep and multi-target circuits over
recalling after one safe kill. Before an imminent level, issue `train` for the
class profile's current primary stat and wear all legal stat-improving gear.
For generated source-ranked hunts, chain up to three fixed, single-reset,
ordinary targets in one same-area circuit only when every target passes the
normal source and live gates and each short inter-target path excludes
useful-band aggressive or combat-capable special-procedure reachability.
Allow up to 20 source-safe same-area steps between fixed circuit targets; live
level-24 frontier analysis showed that the former 12-step cap rejected an
18-step Solace lieutenant-to-Alex pair and chose an 81-step singleton trip
instead. The larger bound does not relax route hazards, target isolation,
`consider`, health, or exact-selector gates.
Source-proven nonattacking specials may be transit-only hazards; economic
specials additionally require the existing bounded carried-coin exposure, and
the live crowd gate still applies in every target room. Tag every kill with its
source mobile VNUM and generated policy ID. Recovery need, not the first kill,
normally ends a productive circuit. If only one in-band target can be
killed before health, mana, or movement forces recovery while another vetted
target remains, persist that as combat-readiness evidence and audit equipment,
trained damage or mitigation capabilities, and the active rotation. While that
same-level marker remains active, exclude the exact exhausting source policy,
force one fresh class-trainer audit even when the ordinary per-level audit was
already recorded, and prefer the largest viable lower-peak-damage source
circuit before raw XP score. Record the completed training and gear audits on
the marker, but clear it only after at least two objective kills or a level
gain; an audit by itself is not proof that throughput improved.
A generated circuit applies the full departure-health gate only before its
first target. After an objective kill, ordinary later stops use the 22.5%
field-continuation floor; stops with specials, sanctuary requirements, or
bounded peak-damage exceptions retain the 67.5% high-risk floor. Live run 4683
validated this at level 10: Aeloria killed Gnome treasurer 1521 for 276 XP,
continued at 129/145 HP, killed cook 1526 for 248 XP, and returned to healer
room 3054 at full health. The two-kill circuit earned 524 XP in 114 seconds.
After loot, use the same 7.5% mana and 5% movement continuation floors; never
fall back to the old 30% mana recovery gate while a kill-budget-eligible target
remains. Scan past targetless locator or transit stops to the next actual
combat stop before deciding that the circuit is over. Live run 4692 exposed
the stale mana gate by recalling at 87/382 mana after one kill; campaign policy
revision 153 clears throughput markers produced by that obsolete boundary.
When the kill budget is already exhausted, return normally and do not report a
fictional next-target recovery failure.
A failed live `consider` at one generated circuit stop must preserve that
policy-specific evidence and advance to later independently tagged stops. Recall
only when no vetted stop remains or the stop explicitly requires abort after
rejection.
Key generated-circuit `consider` and below-band evidence by the active stop's
source policy ID, mobile VNUM, and reset room. Never assign a supplementary
stop result to the primary route merely because both ran in one segment. For
legacy transcripts without stop IDs, match only an exact normalized source
identity after stripping a leading article. Campaign revision 151 repaired
the Fleshmonger level-10 history so cook 9403 remains productive while the
independent cook's boy 9404 remains terminally below-band.
Key absence evidence by the same exact source policy. Presence or a live
`consider` at one supplementary stop must not hide an absent primary reset or
cool down the whole circuit. Live runs 4717 and 4719 exposed the old aggregate
failure at mage level 11: absent Ivan 4409 was retried because the visible,
below-band Bearded Lady and Illusionist made the circuit look present. Campaign
revision 154 began recording each searched reset miss independently. A later
live sighting, `consider`, or kill for that exact policy must clear and dominate
all waypoint misses; run 4721 found and fought the wandering Shire Miller
before it fled through a crowded room, proving that an empty later waypoint is
not target absence. Campaign revision 155 preserves the positive presence and
applies absence cooldowns only to policies never seen during the circuit.
Before any hunt fastwalk from recall, refill the carried water skin in room
3005, drink there, and return north; never rely on a stale in-memory thirst
flag for a long route.
When negative fame makes a shopkeeper refuse food, never bounce between that
shop and the healer. Rank source-direct ground food resets, exclude every food
prototype with a nonzero poison value, bind acquisition to the exact object
VNUM and source keyword, and carry the reserve home before consuming it. Treat
an empty reset as a bounded, reset-specific absence and rotate to another safe
food route.
Before any source-ranked, funding, or coin-stash fastwalk departs from healer
room 3054, sleep until its movement threshold is ready; apply this even when
the route has no combat hunt stops.
Deferred funding routes must honor that initial healer movement gate before
starting class-trainer travel; the funding policy may defer normal resupply,
but it must not bypass the first safe recovery checkpoint.
Any live checkpoint outside Midgaard must select `return-home` before restock,
liquidation, banking, training, or other city maintenance, even when current
HP and movement are otherwise sufficient. Exclude death handling and the
explicit Mud School accessory rooms from this location gate. Live run 4238
showed why: restock correctly refused to invent a Midgaard shop route from
Solace room 10295, but return-home needed to own that transition first.
When a bounded segment reaches its runtime limit, force the existing healer
save-and-quit path to become command-ready even if the latest server prompt
has not yet been observed; cleanup must not expire while a character is
sleeping safely at room 3054.
Tune autonomous field play 50% more aggressively than the original baseline:
tolerate recoverable damage, use 360-second bounded fights, continue circuits
at 22.5% health with 7.5% mana and 5% movement, leave the healer at 37.5%
health and 15% mana, ordinarily withdraw at 15% health, and finish a
lower-level half-dead opponent down to 10%. Retain a 67.5% departure floor
for high-risk and aggressive targets. Keep death traps, unknown high-level
enemies, unsafe crowds, disabling affects, and unsupplied hunger or thirst as
hard withdrawal boundaries.
For every source-ranked combat stop, also carry the source-derived maximum
critical damage of one NPC hit. DD4 criticals double one ordinary hit; when
that verified burst can kill at current HP, raise only the active stop's live
withdrawal floor to the burst ratio. Otherwise retain the aggressive 15%/10%
thresholds. Do not blanket-reject armed, high-XP targets: preserve explicit
bounded peak probes and research pools, and let source, live consider, gear,
protection, and reward evidence balance risk against XP per trip. When a safe
fixed-reset area offers multiple isolated targets, rank the whole circuit by
risk-adjusted source reward per outbound and inter-target travel step. A
wandering high-score candidate must not suppress that circuit merely because
it ranked first as a singleton. A death during a source-ranked attempt is
fatal evidence for the exact mobile VNUM, reset room, character level, and
reboot, including when an objective kill was recorded before the death and the
net attempt lost XP. Preserve that kill as forensic evidence, but block blind
retries. Tag objective kills by exact source identity so incidental transit
kills cannot inflate progress or promotion evidence.
Balance risk against throughput rather than minimizing death probability alone.
An expired absence or retryable probe is not progress evidence: when a
same-reboot source route has a meaningful measured XP return, let that
productive repeat outrank the retry unless the fresh route has materially
stronger risk-adjusted reward evidence. A no-flight fallback must not displace
a productive route solely because it avoids buying flight; preserve the normal
source, live-consider, crowd, health, protection, and return gates while
optimizing expected XP per travel step.
Quantify the fresh-route exception: a fresh candidate may displace a
productive repeat only when its risk-adjusted source score per travel step is
at least 25% higher. The score is a route reward proxy with a soft peak-damage
penalty, not a replacement for live gates. Keep the requested mobile's own
aggressive reset in the risk pool when its route is otherwise source-reachable;
score the aggression as caution and enforce the normal consider, isolation,
health, protection, equipment, and return checks instead of rejecting it solely
for being aggressive. Other aggressive route or companion hazards remain hard
blocks.
Live run 5402 validated this balance for Dorrik: Bardoosh mobile 4515 in room
4514 produced 671 objective XP and 851 XP total after three incidental 60-XP
goblin kills, then returned safely to healer room 3054 at full health and
movement. Runs 5392 through 5401 remain recovery, maintenance, or low-value
contact evidence and must not be misreported as equivalent progression.
Run 5403 then selected Aruncus the Druid, mobile VNUM 300 in reset room 323,
for 505 objective XP and a full healer return. Dorrik reached 101,307 XP;
this is productive level-15 evidence, not merely a safe recovery.
Run 5405 repeated Bardoosh mobile VNUM 4515 for 351 objective XP plus one
incidental 70-XP goblin kill, returning at full HP and 264/290 movement. Keep
the repeat eligible while its tagged reward remains meaningful and its live
gates continue to pass.
Run 5406 repeated Aruncus mobile VNUM 300 for 462 objective XP and returned
at full HP and 269/290 movement. Continue this productive repeat while its
measured reward remains meaningful; do not let an empty unrelated route or a
generic safety preference displace it.
Run 5407 found fanatical goblin guard mobile VNUM 4516 wandering into room
4522; Dorrik killed it for 264 XP after absorbing a critical hit and returned
safely for healer recovery. The transcript proved the exact live VNUM even
though the registered reset-room stop used a different display name, so retain
wandering kill attribution by source identity rather than by room label alone.
Run 5408 accepted the measured Bardoosh repeat: mobile VNUM 4515 yielded 460
objective XP and a wandering goblin added 70 incidental XP. Dorrik returned
without death or flee at full 322/322 HP and 279/290 movement. Treat this as
productive risk/reward evidence and keep the repeat eligible while its tagged
reward remains meaningful; do not optimize for zero damage or zero incidental
encounters when the live withdrawal and return gates still pass. Run 5409 then
selected Aruncus for 421 XP in 69.8 seconds and returned at full HP; run 5410
reopened the cooled Shargugh route and confirmed it absent. Runs 5411 and 5412
were required flight/provision maintenance and must not be counted as XP work.
Run 5413 reached Bardoosh and SQLite events recorded a 60-XP goblin-lieutenant
interruption plus a 460-XP Bardoosh kill, but the worker was stopped after its
transcript stayed empty; run 5414 recovered safely at 103,935 XP. Keep the
interrupted segment failed until its kill metadata is reconciled, and close both
the segment and its unbound run record during process recovery. Persist each
recognized mob kill and loot sale immediately while the run is active, not only
during normal runner cleanup. Recover an interrupted source-ranked objective
from the run-scoped kill ledger only when its exact `source_policy_id` matches;
never promote an incidental kill. Run 5417 proved that a kill row was externally
visible while its run still had status `running`. Run 5415
confirmed both Shadow Keep Wraith rooms absent after one incidental 60-XP goblin
interruption; do not promote that result. Run 5416 then reopened fanatical
goblin guard mobile VNUM 4516, earned 257 objective XP, and returned at full HP
with 281/290 movement. This is an approved higher-risk repeat because the
reward remained meaningful and the live withdrawal/return gates passed.
Run 5419 then killed the same source-matched guard for 286 objective XP plus 70
incidental XP and returned full at 104,728 XP. A confirmed objective kill must
force target-presence evidence and clear stale target-absence state before the
segment and campaign snapshots are serialized.
For source-ranked throughput, count progress only from objective-kill evidence,
not the character's aggregate XP delta. Incidental transit kills must not reset
the no-progress streak, clear unrelated absence evidence, or become the current
policy's productive XP result. Apply the same calculation during a live
multi-segment process and when reconstructing after restart. Runs 5420 and 5421
earned 60 and 10 incidental XP with empty objective-kill lists; the repaired
two-segment streak forced a measured productive repeat, and run 5425 killed
mobile 4516 for 303 objective XP before returning safely at 105,161 XP.
Do not let the generic non-fastwalk 25% emergency-resupply floor override a
field fight's 15% withdrawal or 10% finisher threshold.
For a return-home checkpoint at the healer, use the same 90% movement floor
both when deciding to sleep and when deciding to wake. A lower generic wake
floor creates a no-progress sleep/stand command loop.
After a completed field hunt reaches healer room 3054, recover to the same 90%
movement floor before save and quit. The lower field-ready reserve may carry a
return through Midgaard, but must not force the next campaign segment to spend
a separate connection on healer recovery.
For bounded live HERO invocations that can enter progression combat, set
`--max-segment-runtime` to at least 420 seconds so the 360-second combat bound
still has travel and healer-cleanup time. Live run 4211 proved that 240 seconds
can preempt a healthy near-finished fight and force an unnecessary XP-losing
recall.
Do not count source-proven or live-level-confirmed below-band mobiles as an
unsafe crowd. They must not block selection of a useful-band target or trigger
a flee while a planned useful-band fight is still unfinished. Never select them
deliberately for XP, but finish unavoidable trivial combat so it cannot stall the
productive hunt. Once the bounded objective kill budget is complete, this
exception ends: flee immediately from any unplanned attacker, including a
below-band one, because there is no remaining objective worth the exposure.
Live run 4564 killed both Solace circuit targets for 2,923 XP, then stayed against
mobile 10215 because its live level was only 13. Its `spec_guard` headbutt and
kick bursts killed Kestrel and turned the segment into a net XP loss; an early
post-objective flee is now mandatory.
For static required-loot circuits, derive trivial bystanders per destination
room from the source movement graph and the current character level. Do not use
a world-wide display-name level range when source reachability can distinguish
the local low-level prototype from a dangerous namesake. Live run 4654 used
this gate to ignore the level-1 teddy and level-3 toy soldier, kill an old doll
and the nanny for 151 XP, and return Dorrik safely at full health.
For source-ranked room isolation, include a trivial same-area wanderer only
when its source movement graph can reach the live room. Before ignoring its
normalized short identity, prove that no materially dangerous source mobile
with the same identity can also reach that room; generic names such as
`citizen` must never mask an ambiguous dangerous prototype. Build this
reachability index once for the complete circuit, never once per destination;
the White Stag's 38-stop graph exposed minute-scale CPU stalls from per-room
world scans before the inverted index correction.
When the bot opens a source-closed door, live movement can place an ordinary
wanderer outside that static graph. In that case, permit an area-scoped
fallback only when every same-area reset prototype with the normalized live
identity is source-proven trivial at the current level. Campaign revision 157
adds this boundary after run 4730 found Granny Jenkins with a harmless level-5
New Ofcol citizen in room 600; a dangerous same-name prototype still preserves
the crowd rejection. Live run 4744 validated the repair: the citizen no longer
made Granny Jenkins appear crowded, while her below-band live `consider` still
prevented combat independently.
Apply the same reverse-reachability proof to global wanderers whose source
movement can cross area boundaries. Ignore only an exact trivial identity that
can reach the destination, and retain it as a crowd when any dangerous
same-named prototype can also reach that room. Live run 4678 exposed wandering
Midgaard Fidos and a vagabond inside the Circus; campaign revision 150 reopened
the resulting false crowd result for the Bearded Lady and Illusionist circuit.
Treat duplicate same-prototype targets as a possible assist crowd: `fight.c`
allows an idle mobile sharing the engaged mobile's prototype to join
probabilistically. Skip that stop and continue to later registered circuit
rooms; do not let a matching target in the old room satisfy the next routed
stop before its destination is reached.
For a source-ranked mobile proven by `MobileSource.wanders` to move, do not
discard a full circuit merely because the target enters a crowded room. Remain
standing and re-run `look` at 12-second intervals, deriving three to eight
attempts from the number of source-reachable exits. This mirrors the four-second
`mobile_update` and 1-in-32 chance per usable direction, targeting about a 50%
chance that the mobile leaves while keeping the live segment bounded. Retain
every normal source, identity, isolation, health, and live-`consider` gate, and
cancel the wait immediately if combat starts.
Live run 4601 validated the timer against Mirror Realm mobile 19022 in the
one-exit Travellers Shop: three 12-second looks remained safe but did not move
the gardener. Source `update.c` then justified the exit-weighted three-to-eight
look budget. The same rotation continued productively in run 4603, where
Kestrel killed Mahn-Tor mobile 2301 for 1,137 XP and returned to healer room
3054 at 274/334 HP without consuming the reserved sanctuary potion.
For Mirror Realm fame recovery only, treat an unrelated wandering mobile in
the buck or moose room as potentially transient. Remain standing, re-run
`look` up to three times at 12-second intervals, and apply the full source
identity, isolation, health, sanctuary, and live-`consider` gates after every
refresh. Any combat interruption cancels the wait immediately. If the room is
still crowded after the third refresh, preserve the normal retryable crowd
result and return to the healer without consuming the sanctuary potion.
Treat an unapproved attacker that joins after combat starts as the same
retryable crowd condition: flee, recover, discard the interrupted research
result, and recheck the source target on the next bounded segment.
When productive work ages an absence or crowd cooldown, reconnect metadata
repair must preserve the remaining count. Historical positive-kill recovery
may restore the policy result, but crowd evidence on that same kill segment or
on a later durable segment still owns its already-decremented cooldown; never
reset it to the default merely because the positive evidence was reconstructed.
Run 4533 both killed the Solace lieutenant and ended crowded at Alex. Run 4544
then reduced that cooldown from three to two at checkpoint 11429, and the fixed
live reconnect preserved two through checkpoints 11430-11433.
Historical clear-marker recovery is event-specific: only an explicit
`research_policy_retried` checkpoint may restore `campaign_cleared_research_policies`.
`campaign_metadata_repaired`, `source_policy_rotated`, and segment-complete
snapshots are derived state and must not be replayed as new clear decisions. If
protection recovery is required while its sanctuary policy is on cooldown,
report that protection wait before applying unrelated crowd or reset handling.
Before HERO renaming is available, use source-backed keywords and keep active
gear directly accessible; put spare ambiguous items in containers or the vault.
Never guess object or mobile command keywords when the entity exists in the
public source. Parse and use its source keyword list; display-text noun
inference is only a temporary fallback for genuinely uncatalogued live
entities and must not be promoted into policy without source confirmation.
Choose wear, wield, remove, get, and similar selectors against every carried
source-matched object, including potions and other non-gear. Live run 4403
proved that `wear blue` selected a light blue potion before blue snakeskin
boots; `wear snakeskin` is the unambiguous command. Treat `You can't wear,
wield, or hold that.` as a completed failed gear command so it cannot become an
`eq all`/wear loop.
Enable DD4 `TARGETMODE` before a combat fastwalk. Bind each live `[#number]`
selector only to a mobile whose target-mode line matches its source room
description, and use that exact selector for `consider`, the combat opener, and
targeted combat actions. Never promote an object selector into the mobile map,
persist a live selector across connections or reboots, or replace the reusable
source identity in policy/evidence with an ephemeral selector.
When the complete source mobile catalog is loaded, count only live room lines
that match a catalogued mobile description. Do not run the generic mobile-prose
parser over unmatched lines: TARGETMODE also numbers objects, and ordinary room
prose may contain mobile-shaped verbs. Live run 4533 reached Alex in Solace but
misread `Metal and wooden objects are everywhere.` as a third mobile; the
source-only count retains Alex and the harmless below-band townguard without
inventing that phantom crowd.
When a registered wandering target appears in any source-vetted room while its
circuit is active, stop before the next route step and run the normal crowd,
health, level-ceiling, and `consider` gates against that live selector.
Apply this interception during destination-guided field circuits as well as the
official outbound fastwalk, but only when the current room VNUM belongs to the
active stop's registered route graph. Live runs 4227 and 4235 exposed Old
Thalos lamias walking through those safe transit rooms while endpoint-only
searches missed them; source confirms every mobile-5201 lamia reset equips the
required long slim dagger.
Do not apply the reset-endpoint VNUM restriction to that bounded circuit
interception: the source mobile VNUM identifies the registered prototype, while
an ordinary non-sentinel mobile may have wandered to another room in the same
safe route graph. Still require its exact source display line and fresh
TARGETMODE selector. Live run 4253 saw mobile 5201's lamia twice in Thalos room
5212 and exposed the obsolete endpoint-only guard before the corrected worker
was loaded.
DD4 mobile arrival notices do not include a TARGETMODE selector. When an exact
active source target produces `<target> has arrived.` in a source-vetted route
room, pause navigation for one `look`; only the resulting source-matched room
line and fresh selector may enter the ordinary interception gates. Do not treat
the arrival notice itself as combat authorization. Live run 4616 saw the large
hobgoblin enter Moria room 4063, but the pre-fix circuit continued navigating
and returned without its sanctuary potion.
Use the source parser's canonical `strange lamia` identity for this exact
target while retaining `lamia` as the explicit `where_target` and command
keyword. Live run 4273 exposed the combat mismatch: the circuit saw many valid
selectors but a policy targeted only as exact `lamia` rejected all of them.
Live run 4293 then exposed the inverse locator mismatch: `where lamia` reports
rows as `The lamia`, so parsing them as exact `strange lamia` waited until the
watchdog. Live run 4304 proved both identity fixes, then exposed a movement
race: selector `#3416` appeared in room 5239, but the lamia left south in the
same response before `consider` arrived. Remove that stale selector, follow
the observed direction once through the registered route graph, and require a
fresh exact line and selector before considering or attacking. Live run 4307
then found two exact lamias together in room 5239. Treat that duplicate
same-prototype room as a skipped stop and continue to later registered circuit
rooms; do not turn the local assist risk into an immediate circuit-wide
recall. Live run 4309 validated the complete recovery: the circuit found an
isolated lamia at selector `#3398`, disarmed and killed it for the intentionally
below-band 80 XP, looted object 5252, verified the long slim dagger in the
primary weapon slot, and returned at full health to healer room 3054. Apply the same canonical contract to the Forest `kodiak bear` and
Moria `garter snake`; their longer room prose is not the parsed mobile
identity.
Apply the same bounded pursuit when an engaged target flees: live run 4673
reduced Circus mobile 4409, Ivan, from 106 to 57 HP before he fled east, but a
cleared live-enemy identity prevented the old detector from following him and
six stale `kill #2923` commands triggered the watchdog. Campaign policy
revision 149 recognizes an observed departure after combat has started even
when GMCP has already cleared the active identity, removes the stale room
selector, and follows the legal adjacent exit for a fresh room safety check.
Treat a seen or considered target as positive evidence even when it survives:
never propagate whole-circuit absence to supplementary resets. Revision 149
repairs the primary as a retryable present attempt and reopens any unvisited
supplementary targets; run 4675 confirmed the repaired checkpoint before a
productive two-kill, 495-XP Fleshmonger repeat and safe healer return.
When different mobile prototypes share a short description, preserve the
source-distinct identity from the room line and keyword list (for example,
male versus female `a centaur`). Use the generic short name only for the
area-scoped `where` preflight; for source-ranked stops also require the
candidate's exact normalized source room display line before considering or
attacking a live selector.
Persisted GMCP inventory descriptions may still contain an ephemeral
`[#number]` prefix from the connection that recorded them. Strip that prefix
before source-catalog matching, sale planning, equipment comparison, and
liquidation signatures; never treat it as part of an object's identity. Live
run 2047 validated that this recognizes Aruncus's no-drop strange amulet,
triggers `heal curse`, destroys it, and disposes of the remaining unsellable
loot safely.
DD4 can also emit malformed `Char.Items` JSON when a scroll description contains
unescaped quotation marks. Keep the structured parser as the first path, but
fall back to a bounded item-entry recovery that preserves quantities and
`[#number]` selectors; otherwise a newly purchased pie can disappear from the
food reserve detector and cause a needless funding loop. Cover this fallback
with a fixture derived from a redacted live payload.
For source-ranked wandering targets, first follow the source-backed path from
any fastwalk staging room into the target area's source endpoint, then issue a
source-keyword `where` preflight. Require an exact source identity in the
response: related names such as `Farmers guarddog` do not locate `The Farmer`.
A miss from a staging room or another area is not presence evidence and must
not mark the target absent. Once inside the target area, if DD4 returns `You
fail to find anyone by that name.`, or lists no exact target, mark it absent
from the current area and recall rather than enumerating the full area. For a
global wanderer this is current-area evidence, not a reboot-wide absence claim;
rotate to another candidate and retry later. If `where` reports a presence,
retain the bounded source-room search. Treat the reported room as a snapshot,
not a guarantee. Collapse differently named intermediate rooms into
movement-only legs, inspect every safe room in the mapped name group, then
refresh `where` once from the actual current room using source routes generated
for every safe origin. Do not blind-sweep the remaining differently named
rooms first. Preserve the complete waypoint sweep only for legacy locators
without a safe relocation graph. Run 5516 spent its 240-second boundary on 42
Aruncus destinations; the repaired `Grassy plains` group requires seven target
checks. Live run 2048 spent about 290 seconds searching for a globally absent
Kodiak and motivated the original gate.
Treat source-program messages that forcibly relocate the character as hard
route hazards. Record the relocation, stop the stale route immediately, and
recall even if GMCP omits the post-transfer room snapshot; never retry doors
or route steps from the pre-transfer location.
If a live field step reports that swimming, flying, a boat, or an accessible
door is required, roll back that waypoint and record the route hazard. Skip
only the blocked registered stop and continue the bounded circuit when a later
source reset remains; if it was the final stop, return immediately. Never wait
for the inactivity watchdog before trying the next safe location or policy.
Treat any pending movement response of the form `The <source name> is closed.`
as a dynamic exit, not only `door` or `grate`: roll back the exact route index,
issue `open <direction>`, and retry. If the named exit reports locked after the
open attempt, stop the stale route and recall. Run 5518 exposed this with `The
brush is closed`; its watchdog returned Dorrik safely before the generic parser
was repaired.
Do not let one borderline aggressive transit reset permanently hide a deeper
source-safe circuit. It may be crossed only when its maximum source-fuzz level
is exactly `character level - 4`, the prototype has one global reset instance,
no special, fame, shopkeeper, or no-XP flag, and its maximum peak round and
critical hit are each below current max HP. Require live GMCP level evidence:
finish it only below-band, and flee from a useful-band roll. Run 5512 validated
this with Ambush mobile 4516 before a 622-XP Haglik kill and a safe healer
return.
Treat profession-visible empty `eq all` slots as equipment debt. Prefer usable
mob drops, then inexpensive class-legal Midgaard basics; after major gear loss,
revisit Mud School first and repeat its course to recover free starter drops.
Count required replacement gear across both carried inventory and the
authoritative worn paper doll. A worn item satisfies its share of a duplicate
quantity requirement; never attack a carrier for an item already worn. Run
5499 proved that one worn pink ice ring leaves only one ring missing and a worn
linen robe removes the nanny branch.
Never wear a finger item that applies a strength penalty. For low-level
characters with two legal finger slots, prefer two pink ice rings; each gives
+1 strength and +6 hit points. Only the old-doll reset in Dwarven Daycare room
6605 equips object 6601. A same-vnum doll loads without a ring in room 6604 and
may wander into 6605, so verify the corpse drop and use the bounded
three-productive-segment retry after killing a non-carrier. An empty oversized
container may be lodged temporarily to make room for required drops only after
`look in` proves it is empty.
A thief whose best accessible piercing weapon is still materially weaker than
Forest object 18000 must retain the bounded kodiak upgrade through level 29.
The claws are source type 5 weaponry, not a body-part object: they deal 6d12
piercing damage and add +3 hit roll. Keep the three-productive-segment cooldown
after an absent bear and stop retrying as soon as carried or worn gear matches
or exceeds that source damage score. A `where kodiak` result of `River bed`
does not authorize pursuit: those rooms hold the excluded aggressive mosquito
and wasp resets.
When that Forest attempt is cooling down and a thief still uses a weaker
piercing weapon, use the Old Thalos intermediate tier. Object 5252 is a 2d5
long slim dagger with +1 hitroll and +1 damroll, carried by source-level-9
lamias. Issue `where lamia` at the official route endpoint, then search only
the registered lamia-only reset rooms. Keep this tier's retry cooldown
independent from the Forest cooldown. Live run 2128 acquired and equipped the
dagger after recovering from a combat disarm, raising damroll from 3 to 4
without taking damage. During `rearm-primary-weapon`, inspect the wield slot
after `eq all`; for a thief, directly wield a carried source-matched piercing
weapon before considering a shop trip, and never accept an arbitrary wielded
weapon as the primary when backstab gear is available. Live run 2338 verified
the persisted long slim dagger, exact-selector backstab, a 484-XP nobleman
kill, and safe healer recovery after this maintenance gate.
Old dolls from the room-6604 reset can wander north into room 6603, but that
reset has no `E 1 6601` ring load. Observe or bypass those wanderers; do not
use them as a pink-ring required-loot exception. The room-6605 reset loads two
mobile-VNUM-6605 dolls and applies its single `E 1 6601` ring load to the last
created doll. Enter room 6605, use the last exact TARGETMODE selector, and
perform one carrier attempt per area reset. Keep the second finger objective
for the existing reboot-local retry cooldown rather than killing the other
10-XP doll without a possible ring. The room-6602 nanny's separate `E 1 6621`
reset remains valid for the linen robe. Source evidence comes from
`daycare.are` at DD4 revision `f2491fd`; do not infer a second ring from the
mobile reset capacity.
When a static required-loot `FieldHuntStop` has a known source reset room,
record it as `source_reset_room_vnum`. The route may pass through a waypoint
where the same mobile has wandered, but field interception and ordinary target
evaluation must wait until that registered room. This endpoint gate is generic
and must not be replaced with character-specific target handling.
An absent or crowded ring carrier is a temporary area-state miss, not a
reboot-scoped failure. Rotate through three productive field segments before
retrying the Daycare ring recovery during the same reboot; a reboot permits an
immediate retry. Policy-revision migration must preserve an in-progress retry
countdown, and below-band evidence from a required-loot nanny or doll must not
exclude `recover-daycare-ring` itself. Runs 4738 and 4760 respectively proved
the countdown decrement and the repaired exclusion-free live retry.
A registered one-off gear recovery may attack a source-proven low-level carrier
after a below-band `consider`, but must record that the kill is solely for a
required missing item and never treat it as an XP policy. Do not consume a
sanctuary potion for that deliberately below-band required-loot kill; preserve
protection consumables for progression combat.
For mages below level 25, `summon familiar` is a verified source-backed
risk-control opener. The spell cannot be used indoors or underwater, costs 100
mana, creates the level-15 no-experience pony from `mounts.are`, and must be
followed by `group pony` and `order pony kill <exact target selector>` before
the player's opener. Run 7638 proved this sequence against Bardoosh. Keep the
familiar path outdoors and source-ranked; do not spend it on trivial
required-loot kills. Because DD4's `group_gain` does not reward a summoned NPC's
final blow, order `pony flee` once the exact target reaches 45% HP or less;
mark the familiar unavailable for the remainder of that segment and fall back
to the normal protected opener if summoning or withdrawal fails.
Leave a depleted hunt area before waiting because occupied areas reset more
slowly.
Use the recorded per-policy XP delta to rotate away from zero-XP field
segments; in particular, an empty Circus segment at level seven must not send
the next run back to an already empty Moria circuit.
Before an imminent level, select a source-backed training stat and skip any
stat whose parenthesized permanent score is followed by `+`. Prefer
constitution for low-level martial characters because it directly increases
hitpoint gains.
Do not fall back to Mud School after live `consider` evidence shows its entire
opponent set is below the useful XP band. Level-eight thief and warrior
campaigns rotate the registered three-target Circus policy with the isolated
Moria large-orc probe and the three-stop Gnome guard circuit. Engage a Gnome
guard only when it is the room's sole mobile and passes live `consider`; reject
duplicate guards or a guard accompanied by any wanderer. Keep
the Miden'nir Ambush exterior research-gated because a wandering dark horseman
can join otherwise suitable combat.
Level-seven Gnome campaigns continue from the hermit to the isolated miner
resets in rooms 1563 and 1565; each stop retains independent crowd, live
`consider`, health, mana, movement, and encumbrance gates.
At thief level 13, rotate an empty Aruncus sweep through Fleshmonger, then
return to Aruncus. Do not repeat Bardoosh after a completed no-kill combat
probe until backstab becomes trainable or materially stronger gear changes the
matchup. At thief level 16, one empty Rock Toad circuit may trigger one bounded
Bardoosh retry only after the generic progression path has prioritized
backstab and a stronger piercing weapon. Preserve the exact-target, live
consider, 90% health, +1 live-level, sole-target, disarm recovery, and healer
return gates; never immediately repeat this fallback. Live run 2209 proved the
new capability boundary: repeated knife attacks and automatic long slim dagger
recovery killed level-12 Bardoosh for 535 XP without Kestrel taking damage,
returned three saleable drops, and finished at healer room 3054 with full
health and movement. This positive kill promotes a reusable level-16-only
hunt. Select it after a Rock Toad segment has given Ambush time to reset
outside the area, including a non-actionable Toad pass when Bardoosh's latest
verified result remains productive, then rotate back to Mahn-Tor after every
Bardoosh pass. A zero-XP verified Bardoosh result blocks another Bardoosh
retry.
Maintenance such as flight purchase, optional weapon recovery, and loot sale
must preserve this last-progression-policy cadence. Live run 2217 proved the
preserved transition across two maintenance passes, killed Bardoosh for 474 XP
without player damage, and returned three drops to healer room 3054. Run 2219
then proved the required reverse transition through loot-sale maintenance,
killing a level-13 Rock Toad for 303 XP and returning safely. Runs 2224 and
2225 correctly rejected three crowded Toads but exposed an immediate zero-XP
repeat; run 2226 proved the corrected rotation by killing Bardoosh for 517 XP
and returning safely at full health.
Keep optional-maintenance fastwalk results out of generic research metadata.
Preserve their dedicated retry cooldown, but clear transient crowd, absence,
consider, and abort fields before checkpointing so the retained last XP policy
cannot inherit a maintenance-room outcome. Runs 4653-4654 exposed and verified
this separation for Dwarven Day Care ring recovery at policy revision 145.
If a specialized opener such as `backstab` or `shoot` is rejected while the
exact target remains present, immediately retry once with normal `kill` using
the same TARGETMODE selector. During recurring combat actions, treat a changed
GMCP enemy HP snapshot as watchdog progress; unchanged enemy and character
state must still retain the bounded repeated-command watchdog. Live run 2215
proved both behaviors by finishing a suspicious level-13 Rock Toad for 395 XP
without a false watchdog withdrawal.
An Aruncus sweep starts in reset room 323, then immediately checks room 330 and
opens the west door into Hermit's Hut room 331 before traversing the outdoor
circuit. Live run 2037 proved that `where aruncus` can report the hut while an
outdoor-first search consumes the entire movement reserve. Sorbus is a
source-level-four non-aggressive bystander there and must not block the exact
Aruncus selector. Live run 2041 validated both door directions, a viable
room-318 fight, one bounded flee pursuit, a 541-XP kill, and safe healer
return. Live run 2044 validated the exact hut-present case: the route entered
room 331 immediately, accepted Sorbus as harmless, killed Aruncus for 538 XP,
and safely saved and quit in healer room 3054. Live run 2045 proved that
immediately repeating this single-reset hunt wastes 320 commands on an empty
circuit. After a successful kill, rotate to a current-reboot viable outside
area such as the Gnome treasurer before retrying Aruncus. At level 14, Kestrel has no
recurring thief attack because the trainer
caps Stealth Techniques at 56%, below backstab's 60% prerequisite; do not
misdiagnose normal-only combat as a runner fault until that cap clears.
On the Bardoosh circuit, treat the Miden'nir wyvern as an allowed non-attacking
bystander: source revision `d7cb330` defines it at level 8 without
`ACT_AGGRESSIVE`. It has `spec_poison`, so do not select it, but its presence
must not trigger a flee from a lone forced goblin or goblin lieutenant fight.
The Ambush route reaches the sentinel goblin archer in room 4515, then goes
`west` to Bardoosh's reset room 4514; do not infer this final step from the
duplicate mobile/room VNUM values or the rooms' shared display name.
When a source mobile has an explicit proper short name but a generic room line,
bind the TARGETMODE selector to the proper source identity. In particular,
`A goblin is here sleeping.` in room 4514 is Bardoosh, mobile 4515.
At level 13, Bardoosh is evidence-valid but inefficient until backstab becomes
trainable: live run 1902 gained 257 partial-combat XP, paid 132 XP to flee, and
completed no kill. Record runtime-capped no-kill segments as zero effective
policy XP and rotate back to Aruncus rather than forgetting or immediately
repeating the attempt.
Keep the level-14 Dwarven Kingdom worker route passive. Live run 2022 found
perfect-match workers, but run 2023 proved that the source-level-16 giant can
wander from an adjacent room and assist an apparently isolated fight. Worker
combat is retired; do not promote it without an adjacent-room threat gate and
new bounded evidence.
The level-14 Gnome treasury loop may traverse the crowded hobgoblin-soldier
approach but must not attack there. In room 1570, collect both source-keyed
`coins` piles, then attack at most one exact, isolated treasurer only after a
fresh viable `consider`. Scope pile values to the current reboot. Live run 2038
earned 282 XP without taking damage and returned safely after one kill.
At thief levels 14 and 15, the verified Mahn-Tor Rock Toad circuit checks rooms
2311, 2313, 2312, and 2319 independently. With a sanctuary potion, kill at most
one viable target. Without a potion, a second isolated target is allowed only
when the first kill leaves the existing continuation gates satisfied.
Each target keeps exact-selector, single-mobile, live `consider`, and +1
live-level gates. One purple potion protects only the first fight, so return
after that kill instead of entering another toad fight unprotected. The level-10
thief guildmaster caps second attack at 65% for Kestrel at level 14; persist the
live trainer-cap rejection until he levels. After a toad segment nets at most
250 XP and no sanctuary reserve remains, run the verified Moria large-hobgoblin
acquisition pass. Inspect only source reset room 4064, reached directly by
descending from no-mob room 4020. If the carrier has wandered, return and defer;
do not continue west into the aggressive maze circuit. Admit only a live
carrier above the prohibited diff <= -5 branch, stow its purple potion in the
worn pouch, and require the next toad combat to quaff it and confirm sanctuary
before ordinary damage. Never classify self-inflicted affect damage such as
`Your poisoned blood ... you` as a joining mobile attacker.
Live runs 2129 and 2130 killed Rock Toads with the Thalos long slim dagger in
69.9 and 73.8 seconds, finishing at 212/217 and 194/217 hit points; the
preceding three plain-dagger kills took 104.1, 92.1, and 90.0 seconds. Treat
those two upgraded samples as encouraging evidence rather than a stable speedup
claim.
Live run 2134 proved the campaign reset retry waits outside Moria and can
recover its source-room potion carrier after 60 seconds; the kill yielded 332
XP without damage. Live run 2135 then acquired Kestrel's second pink ice ring,
raising maximum hit points from 217 to 224, modified strength to 17, damroll
from 4 to 5, and carry capacity from 250 to 300. Live run 2137 repeated the
source-excluded `River bed` Kodiak result and returned safely instead of
pursuing into the poison branch.
Live runs 2153 and 2157 repeated that safe River-bed rejection. Run 2163
received only the ambiguous `Forest` locator label, spent about three minutes
searching every vetted room, and returned with zero XP. Retry this wandering
weapon carrier only after six productive field segments; maintenance and
zero-XP segments do not reduce the cooldown.
After a productive Rock Toad segment, rotate to a previously productive
Aruncus hunt or same-reboot viable Gnome treasurer before revisiting Mahn-Tor.
After the single-reset Aruncus hunt, rotate onward to the treasurer or Rock
Toads. Do not erase reboot-scoped evidence of productive Rock Toad kills only
because the latest Toad segment was empty; useful work outside Mahn-Tor gives
its resets time to repopulate. Live runs 2138 through 2140 exposed the waste
from immediately repeating
the cleared Toad circuit and then checking the recently cleared Moria carrier.
Apply the same rotation after a productive one-kill Toad policy whenever the
expanded circuit already has live evidence. A current level-and-reboot
below-band policy exclusion is terminal for selection, not merely advisory;
persist the source mobile VNUM for source-ranked exclusions so sibling reset
rooms for the same mobile are excluded too; never return that mobile or policy
until level or reboot changes. Runs 2146 through 2149
exposed both gaps: an unnecessary expanded Toad pass followed by two checks of
the same below-band Moria carrier.
Provision-funding routes may deliberately use a below-band carrier only for a
source-registered coin or saleable-drop requirement, never for XP. A current
level/current-reboot below-band sighting normally excludes that carrier from
funding rotation, but an explicit flight or provision shortfall may use one
source-safe mobile coin carrier after the normal route, crowd, special, and
live-consider gates remain valid. Keep the emergency choice bounded to the
carrier's observed copper-equivalent value and record it as funding-only.
Prefer fresh coin carriers over ordinary gear carriers, then use observed
proceeds, current cash, and rotated completed routes to accumulate the shortfall;
prototype object cost is not realized sale value. Do not route back to a mobile
whose live gate will only produce another skipped segment. Rotate to another
source candidate or surface an explicit funding-unavailable state. When a
flight shortfall remains after fresh carriers have been exhausted, a previously
successful direct ground coin stash may be re-probed once through its source
route; verify the live currency delta and never treat the non-combat collection
as XP progress.
Mandatory maintenance, including funding, food, liquidation, equipment, and
flight recovery, takes precedence over a productive-hunt handoff created by a
temporary research miss. A handoff may resume ordinary field progression only
after those resource and equipment gates are clear.
If emergency loot liquidation meets an unexpected mobile, flee and return to
healer room 3054, preserve the failed run and transcript, and checkpoint the
current liquidation signature as ready. Do not fail the whole campaign or
immediately repeat that unchanged sale pass; resume it only after new loot
changes the signature.
Treat any forced combat during liquidation or other maintenance as transcript
evidence only. It must not become a campaign objective kill, promote a hunt,
consume a source-mobile kill cap, or count as progression XP policy evidence;
the provision-funding exception is explicitly funding-only.
After a failed flight purchase, a stocked character must select source-ranked
no-flight XP work while its retry cooldown remains, even if current cash is
still below the observed same-reboot price. Decrement that cooldown only after
positive-XP field work, then retry or resume funding; do not repeat a funding
route merely to wait.
If the source-ranked frontier has no eligible no-flight target during that
cooldown, return a bounded unavailable checkpoint. Never recursively reselect
the same flight-required candidate; that is a preflight stall, not progress.
If the current reboot-priced flight potion is already affordable and no
no-flight target is reachable, bypass the cooldown and buy it rather than
launching another funding walk solely to wait.
Also buy optional flight before a source-ranked ground route when the source
estimate is at least 100 movement and flight saves at least 60 movement. A
failed optional purchase must cool down and fall back to the safe ground
frontier without creating a funding requirement. Live run 4187 bought the
reboot-priced potion for 90 copper and confirmed a duration-34 `fly` affect;
run 4188 then reached Kerofk mobile 30248 with 260 movement, killed it for
1,168 XP, and had 348/360 movement before recall.
Never quaff a replacement fly potion while `fly` or `levitation` remains
active: source `spell_fly` returns immediately when `AFF_FLYING` is already
set, so the potion is consumed without refreshing duration. Sleep in healer
room 3054 until the old effect expires, then buy and quaff one replacement.
When all current-band source routes are temporarily unavailable because of
reboot-scoped absence, crowd, or route cooldowns, keep the campaign `ready`
and expose the reset wait; never convert that resumable state to `blocked`.
An explicit bounded retry may reopen the route after waiting outside the area.
If a source fastwalk returns without observing its endpoint, quarantine that
candidate as a route hazard, checkpoint `ready`, and rotate to the next source
route. Migrate an already-recorded failed endpoint checkpoint on resume; never
replay the same broken route indefinitely.
If a source fastwalk progress watchdog repeats a movement cycle without state
progress, treat it as a current-reboot route hazard: preserve the failed run
and transcript, quarantine the candidate, checkpoint `ready`, and rotate after
the bounded productive-work cooldown. Do not rerun the same stalled route in
the next invocation.
For a finite source-ranked hunt circuit, derive an effective command allowance
from its registered route and hunt stops, including a bounded reserve for
combat, loot, return, and healer cleanup. Record any extension above the
profile cap. Keep the allowance finite and quarantine a circuit that exhausts
it; never let the generic profile cap terminate a registered finite circuit
before its final stop, and never remove the hard command boundary.
The same rule applies to optional maintenance fastwalks such as Forest or
Thalos piercing-weapon upgrades: preserve the failed evidence, apply their
existing retry cooldown, checkpoint `ready`, and continue the generic campaign
instead of turning an upgrade-route watchdog into a campaign failure.
Funding routes are waypoint missions: never adopt an unknown or useful-band
aggressive mobile encountered in transit. Preserve any candidate route-hazard
metadata on the generated fastwalk so registered hazards remain active for
funding as well as XP hunts. When an unavoidable transit attacker is
source-proven below the useful band, finish it as incidental combat, then
resume the route; do not count that kill as the funding objective.
Reject funding candidates whose source route crosses a direct or reachable
wandering aggressive reset inside the useful or higher level band. Preserve
below-band route hazards as caution evidence; the runner must finish an
unavoidable source-proven trivial interruption without treating it as an XP
target, so funding cannot dead-end on ordinary Midgaard transit. On a
no-combat funding route, any unexpected useful-band or higher attacker is
terminal for that route: return to healer room 3054 and let campaign rotation
choose the next policy rather than resuming an intermediate waypoint.
For the Dwarven Nobleman fastwalk, the source-level-seven goblin lieutenant is
an allowed below-band transit interruption from level fourteen onward: finish
it only under the ordinary live combat, health, and crowd gates, record it as
incidental, and resume the route. Keep the source-level-eight dark horseman
and wyvern as hard hazards because their damage or procedures can overwhelm a
nominally below-band character.
At thief level 15, use the Olive Grove bandit leader after the level-10
guildmaster cap blocks further progression. The leader wanders among source
rooms 25202 through 25205, so the reset room alone is not presence evidence:
scan the connected rooms and stop when the live TARGETMODE line matches the
source mobile. After an accepted prerequisite gateway, refresh `practice` in
the same room before leaving so newly unlocked skills can be learned. Recall
from this distant trainer and recover at healer room 3054 instead of spending
the field movement reserve on the return walk. Live runs 2098 and 2099 unlocked
and practised backstab; run 2101 then opened a viable level-13 Rock Toad fight
with `backstab`, earned 473 XP, and returned safely. After an empty Aruncus
sweep, run 2104 selected this productive fallback, opened a level-14 Rock Toad
with the exact selector, earned 514 XP, and recovered fully in healer room
3054 before logout.
Sanctuary is opportunistic rather than a prerequisite for the four-room Rock
Toad circuit. Runs 2025, 2026, 2101, and 2104 returned safely
without it. Runs 2110, 2113, and 2114 then ended unprotected kills at 166/217,
206/217, and 150/217 hit points. With no sanctuary reserve, allow at most two
isolated targets while independently enforcing the 40.5% continuation and 27%
withdrawal gates. With a carried sanctuary potion, retain the one-kill cap so
one consumable never authorizes a second fight. If a circuit earns at most 250
XP without sanctuary, attempt one bounded Moria
supply pass; whether or not the wandering carrier is found, retry the circuit
next instead of letting consumable acquisition block productive XP. Run 2105
proved the absent-carrier return path from room 4064. Run 2106 then retained
65 partial XP against a level-15 Rock Toad and withdrew safely, exposing
repeatable damage rather than sanctuary as the immediate throughput blocker.
When consumed sanctuary expires during a generic field fight, do not flee solely
because the affect disappeared. Re-evaluate the live player and opponent HP:
honor the ordinary finish threshold for a target at or below half HP, and
withdraw only at the normal health floor or, when the opponent remains
materially healthier or more than one level higher, below 75% player health;
when both sides are low, compare current HP as well as percentages, while
allowing a nearly dead opponent to be finished.
Special-policy `require_sanctuary` fights use the same health-aware matchup gate
after sanctuary loss: continue a favorable one-on-one fight with a usable live
HP snapshot, withdraw when the matchup is unsafe, and fall back to the normal
character health floor while opponent HP is temporarily unavailable; missing
evidence is not an automatic flee trigger.
For thieves, learn a functional backstab opener, then take the shortest
source-backed recurring-damage path: raise thievery skills to 40% and practise
knife toss toward 45%. `do_knife_toss` is legal while fighting, waits eight
beats, deals level-scaled damage, can double on a face hit, and does not consume
an inventory knife. Issue `knife <exact-selector>` between automatic rounds;
continue the longer disarm and circle chains afterward.
Treat a live segment runtime limit as a soft return boundary, never permission
to close a socket during field combat. Request recall immediately, retry until
combat ends, recover at healer room 3054, and only then save, quit, and finish
the segment. Persist the boundary request and objective-kill evidence.
While a live campaign segment is running, its `campaign_segments.run_id` may
remain null until the segment returns. Monitor the newest matching character
run and its event stream before diagnosing a preflight stall or stopping the
worker; a null segment run id is not evidence that no connection opened.
The Mirror Realm watchman route enters room 19005 after two north steps from
room 19003, opens the reset-closed north door, moves north three times to room
19008, then west into isolated watchtower room 19009. The gardener route
shares that `2n;open north;3n` prefix before turning east. Because the
watchman fastwalk already ends in room 19009, its field stop has no additional
`route_vnums`; never ask the room navigator to find an exit to its current room.
Distinct level-19 mobile 19010 resets alone in the eastern watchtower room
19010 with the same sentinel, stay-area, non-aggressive, and no-special
properties. After probing room 19009, return east to hub room 19008 and move
east into room 19010. Aggregate repeated canonical-target considerations with
logical OR so either independently fuzzed watchman can promote the bounded
one-kill hunt; do not let a later rejection erase an earlier viable result.
The source target parser canonicalizes `The watchman stands here, eyeing you
carefully.` as `watchman`; use that exact identity rather than the prototype
short description `a watchman`. Live run 2188 proved the complete probe and
received the `diff <= 5` consider branch with at least a 100-hit-point
disadvantage for room 19009. Do not attack that instance; probe room 19010
before rejecting the expanded policy for the current reboot. Live run 2200
proved the expanded route and both exact selectors; both watchmen returned the
same `Do you feel lucky, punk?` and `much healthier than you` rejection. The
run entered no combat, lost no HP or XP, and safely checkpointed at healer room
3054, so preserve the expanded policy's nonviable result for this reboot.
Treat the level-16/20 and level-19/20 watchman probe/hunt policies as one
reboot-local reset family: a crowd in either room sets a shared cooldown, so do
not re-enter the other policy name until productive work consumes that wait.
After a nonviable watchman result, probe the Crystalmir White Stag before
Shadow Keep. Source mobile 10012 is level 17 with 15-19 fuzz, evil, unarmed,
non-aggressive, stay-area, and has no special. Require flight for the long
approach. Reach reset room 10016 around the north shore without entering
aggressive Barracuda room 10005, then use the registered GMCP room circuit to
search all 34 low-risk rooms the Stag can occupy. Exclude Fewmaster Toede reset
room 10030 and guard-dog room 10039 as well as room 10005. The first pass is
consider-only; a viable current-reboot result may promote one exact-target
fight with 85% health and a maximum +1 live level offset. Unexpected aggression
from a wandering Fewmaster aborts to healer recovery.
Live run 2203 proved the complete route to room 10016 without combat or damage;
`where stag` confirmed the mobile absent from the current area, so the runner
skipped the long circuit and safely checkpointed at healer room 3054. Treat
this as temporary absence, but account for the route's cost: complete three
productive field segments outside Crystalmir before a bounded retry rather
than rejecting the policy for the whole reboot. Live run 2205 confirmed that
one productive Toad segment was too short a retry interval. Live run 2206
earned 440 XP from one isolated level-14 Toad, skipped a triple-Toad assist
crowd, and reduced the Stag cooldown from three to two without revisiting
Crystalmir. After three productive outside-area segments, live run 2211
performed the authorized retry; `where stag` still reported absence, so it
returned without combat and reset the cooldown to three.
Treat the dynamic no-combat interruption used by older named research policies
as temporary route evidence when it aliases a newer source-ranked candidate;
respect its persisted absence cooldown, then allow the generic source route to
reopen after that cooldown expires. Static source hazards, capability blocks,
and live negative `consider` evidence remain hard exclusions.
The first level-16 fallback is the non-aggressive Shadow Keep Undead Soldier
in room 16615. Its source level is 15 with 13-17 fuzz and it wields a Rusty
Sword, so require a fresh exact-target `consider`, at least 85% health, a
maximum +1 live level offset, and one confirmed kill. A route abort before
`consider` is not target-viability evidence. Live run 2229 proved that an old
aborted-probe rejection no longer suppresses the policy, reached room 16615
safely, and again found the Soldier absent. Require three productive field
segments outside Shadow Keep before another absence retry. The same source
route passes non-aggressive, no-special Shadow Wraith resets in rooms 16603
and 16600. Live run 2237 proved those two rooms after finding room 16615
empty; all three resets were absent. The full exterior circuit also checks the
solitary Soldier resets in rooms 16607 and 16618. From room 16615, follow
west-north-north-west-up, down-east-south-west-west, east-east-east, then
east-south-east. At thief level 16 only a live-level-12 Wraith remains inside
the useful XP band. Promote at most one exact-target kill after a viable
result. On reboot `Sat Aug 1 03:23:54 2026`, run 2252 skipped a duplicate
Soldier pair and promoted the isolated drawbridge Soldier; run 2253 killed it
for 844 XP, recovered from two disarms, and returned safely at 145/233 HP. Run
2255 then traversed the full remaining circuit, skipped the duplicate pair,
and rotated away after finding no other target.
At level 17, after the watchman, White Stag, and Shadow Keep probes are
unavailable, probe Galaxy mobile 9306 in its isolated reset room. Reach stable
Shadow Grove room 1300 by fixed route, then follow live GMCP destination VNUMs
through randomized rooms 1308, 1305, and 1306 and the fixed 9301-9306 chain.
Live run 2291 proved that route without combat or damage but found the reset
absent. A `where white` result in room 9345 is unsafe for this band because that
source room also resets level-31 Cancer; never pursue the white dwarf there.
After an unavailable Galaxy probe, level-17 and level-18 thieves may re-probe
the isolated Dwarven Homestead nobleman under a new band-specific evidence ID.
Source mobile 20504 is level 13 with normal fuzz, non-aggressive, sentinel,
stay-area, unarmed, and has no special. Live runs 1926 and 1931 found a
level-15 instance that was unsafe for level-13 Kestrel but is useful-band for
level 17. Require exact `consider`, at least 90% health, no unsafe bystander,
and a maximum +1 live-level offset. The source-known non-aggressive maid in the
endpoint room is an allowed bystander; a wandering house guest is not. Recall
immediately after a failed consider and
promote at most one kill from the single reset before rotating onward. Live run
2292 got `looks like an easy kill` with only a slight HP disadvantage, but a
level-20 house guest shared room 20506. The no-combat result remains valid;
the hunt must reconsider and enforce its one-mobile ceiling. Do not allow the
guest as a bystander: `fight.c` can make a different-prototype mobile assist
probabilistically even when it is not aggressive.
If a research route reaches its verified destination and the reset target is
absent, do not treat it as a reboot-long viability rejection. Leave the area
and select another executable policy; clear the temporary absence after
productive work elsewhere, using a policy-specific cooldown when the route is
expensive or the mobile wanders widely. Wait outside through the bounded reset
controller only when no alternate policy is available.
For thieves at levels 16-18, fall back to the proven Mahn-Tor Rock Toad
two-kill circuit after both level-16 probes reject. Its source range is 12-16;
retain exact live `consider` at each stop, require the 40.5% continuation floor
for the second target, reject every `diff <= -5` result, and never generalize
the thief combat evidence to another class. Live runs 2257 and 2259 each
completed two isolated kills, earning 1,286 and 877 XP respectively while
returning safely; intervening run 2258 rejected a below-band Bardoosh and
rotated directly back to this productive circuit. Run 2261 exposed an
aura-prefixed TARGETMODE line falling back to a generic keyword; normalize
leading status labels after ANSI removal. Run 2263 then proved exact selectors
for both targets and every knife command. Run 2272 caught the reset after two
empty bounded passes and raised Kestrel to level 17 with two exact-target kills
before returning safely.
At thief levels 17-18, rotate every completed Rock Toad pass through the
verified Aruncus hunt before returning to Mahn-Tor. His source-backed 11-15
live range must still pass exact `consider`; leave weaker `diff <= -5` fuzzed
instances alone. Disable autoloot and manually collect only staff, scroll, and
ivy so object 307, the no-drop strange amulet, remains in the corpse. Live run
2281 killed a viable Aruncus for 612 XP without player damage, restored
autoloot, and saved and quit in healer room 3054.
At critical field-departure encumbrance, sacrifice only registered expendable
loot such as spent Circus keys; preserve food, water, potions, containers,
weapons, and gear unless a separate source-backed replacement policy applies.
When protected spare stat gear prevents an essential food or weapon purchase,
store it in the Midgaard vault before restocking; do not sell it merely to
free capacity. Re-equip the best legal copy from carried gear afterward.
Treat the first vault weight or item-count rejection as terminal for that
storage pass; never remove another item after it. Prefer selling expendable
loot at a compatible shop, then donate or sacrifice registered expendable
objects when they cannot be carried, sold, or lodged. Preserve food, water,
potions, containers, weapons, and best-in-slot gear.
When fewer than ten carry-weight units remain and at least ten individual coins
are carried, bank the coins before considering vault relief. DD4 charges one
weight unit per ten coins, so this may free the required capacity without
lodging protected equipment. Live run 2053 exposed the ordering defect by
lodging a silver circlet at 161/170 weight while carrying 240 coins.
Treat `You can't let go of it.` during sale, donation, or removal as cursed-item
evidence. Prefer a known and usable `remove curse` spell or an identified
remove-curse wand/stave; otherwise return to healer room 3054 and buy
`heal curse`. The spell may toss `NOREMOVE` or `NODROP` objects into the room.
Destroy expendable tossed objects after source or identify evidence confirms
they are not useful; never loop the rejected command. If the healer fee is
unaffordable, take one bounded 500-copper Dragonhoard Bank loan, return to the
healer, and retry once. Live run 2018 verified this flow against Aruncus's
no-drop strange amulet. A room mobile may pick up the tossed item before the
destroy command, so confirm it has left inventory instead of looping.
When source evidence identifies a cursed or no-drop object on a known target,
disable autoloot before combat and collect only approved corpse drops by exact
source keyword. Restore normal autoloot at healer room 3054 after leaving the
cursed object in the corpse. For Aruncus, leave object 307, the strange amulet;
manually collect `staff`, `scroll`, and `ivy`. Live run 2150 proved this exact
flow against live-level-14 Aruncus: the kill awarded 568 XP, only the three
approved drops entered inventory, 15 gold remained unchanged, normal autoloot
was restored at the healer, and the character saved and quit safely. Live run
2154 repeated the behavior against a wandering Aruncus in source room 318,
earned 325 XP, and safely checkpointed without the amulet.
Liquidate the approved Aruncus drops before they create item-count pressure.
Current `midgaard.are` shop data makes the Wizard in safe room 3033 a buyer
for item-type-two scrolls and the grocer in safe room 3010 a buyer for
item-type-19 food. Sell the scroll and poison ivy through those source-backed
buyers; object 308 is item-type-12 furniture despite its `staff` name, so
donate it when no compatible safe buyer exists. Live run 2159 sold three of
each sellable drop, donated three staffs, reduced inventory from 37 to 28
items and 153 to 138 weight, then saved and quit safely at the healer.
DD4's `fwrite_obj` omits `ITEM_KEY` objects from both character and vault save
files, so lodging a key preserves it only until the next save/logout. When a
key is costly or difficult to replace, cache it loose in a source-vetted
`ROOM_NO_MOB` room whose reset residents are neither scavengers nor
`spec_janitor`, and scope that cache to the current reboot identity. Midgaard
bank room 3007 is the registered Circus-ticket cache; try to retrieve the
ticket there before buying and drop it there before logout. A missing cache
must fall back to reacquisition because another player or a reboot may remove
it.
At level 10, stop using the Mud School Loremaster and route each base class to
its source-backed Midgaard trainer, as directed by `HELP TEACHER CLUE`. The
registered trainer rooms are mage 3019, cleric 3002, thief 3029, warrior 3023,
psionic 3150, brawler 3218, shifter 3221, ranger 3048, and smithy 3050. Their
source-defined teacher bases reject lower-level characters. For field-caster
mages, once the shared level-10/11 Fleshmonger guard probe is recorded, use the
protected Moria level-11 hunt as the next progression policy; a zero-XP result
is terminal for that level/reboot until the live evidence is reviewed. At level
10, a zero-XP Moria acquisition rotates once to the mage-specific Fleshmonger
guard-hunt research policy; do not repeat either route without fresh evidence.
If that guard result is nonviable, use the two-stop Moria large-orc research
policy; promote it only after a positive live mage kill, and keep the poison
snake and deeper Moria circuit out of this fallback.
When that research target is absent, persist the reboot-scoped absence and let
the campaign's bounded outside-area reset controller sleep and retry; a new
process invocation must resume that controller rather than launch immediately.
Reset retries are always finite. The CLI and library default to a 30-second
outside-area wait; any longer wait must be passed explicitly with
`--reset-wait`. A retry command must return a checkpoint after its retry budget
is exhausted, and a stale tester process must never be left behind.
When the bounded wait expires, reopen that current research policy before
selecting any reboot-scoped below-band exclusion; an expired absence must never
turn into a hard campaign block or an unrelated target selection.
For thieves, raise Stealth Techniques to its 60% prerequisite, then prioritize
backstab while a piercing weapon is equipped.
At level 15, route thieves to the stronger bandit leader in Argentium Olive
Grove. His source reset is room 25205, but he can wander across rooms 25202
through 25205. Match his source-backed live room line and practise wherever he
is found; if `look leader` fails, defer training without issuing a blind
practice command. His teacher base is 15 and his Thievery, Armed Combat, and
Stealth group caps are 75%, allowing progression beyond the Midgaard
guildmaster's effective cap.
Persist trainer-level practice rejections only for the current character
level. Persist a trainer-proficiency cap across every level that uses the same
source trainer tier because increasing the character's skill cannot make that
teacher stronger; clear it only when the character graduates to a different
trainer. Do not persist prerequisite rejections because another skill learned
at the same level may unlock them.
Treat an `eq all` line containing `[weapon] -` as an empty slot, never as proof
of a wielded weapon. A dedicated rearm run must buy, wield, and verify an
occupied weapon line before succeeding. If the source-backed dagger is
unaffordable, use the existing Dragonhoard Bank credit route, then retry and
return to healer room 3054. If item-count capacity is full, liquidate or
donate safe carried drops before entering the weapon shop; weight capacity
alone does not prove that a purchase can be carried. Live run 5048 exposed
this with two source-matched large clubs hidden behind a retained war-dog
collar; the selector must preserve the collar and free a slot with the clubs.
Runs 5049-5051 validated the repair: the clubs were cleared at healer room
3054, the return-home checkpoint completed, and the subsequent Daycare-ring
maintenance finished safely with Dorrik still wielding his broadsword.

## Development Commands

Use Python 3.12 in the local virtual environment:

```powershell
python -m pip install -e .[dev]
python -m pytest
python -m compileall -q dd4tester tests
python -m dd4tester run scenarios/login.yaml
```

The first command installs the package and test tools. Run the full pytest and
compile checks before publishing a significant change.

## Style And Naming

Use four-space indentation, type hints, dataclasses for explicit data models,
and `snake_case` for modules, functions, variables, and event names. Use
`PascalCase` for classes. Keep protocol parsing, state reduction, storage, and
decision logic in independently testable modules. Prefer deterministic parsing
and structured JSON data over ad hoc text manipulation.

## Testing

Use pytest. Name files `test_<module>.py` and tests `test_<behavior>`. Add
sanitized fixtures for real DD4 output and never include account credentials.
Every bug fix should have a focused regression test. Network access must not be
required by the normal test suite.

## Data And Security

Record commands, responses, GMCP, derived events, state changes, and timestamps.
Use `configure-login` and `configure-character-password` for local credentials;
they use Windows Credential Manager through `keyring`. `DD4_USERNAME`,
`DD4_PASSWORD`, and a profile's password environment variable remain supported
overrides. Transcript and database records must redact credentials. Use direct
Telnet/GMCP for primary testing and reserve Mudlet-in-VM automation for
client-specific validation.
For a new `hero` request, generate a random alphanumeric character password and
persist it under the profile credential name before the first connection; keep
it out of profiles, manifests, transcripts, and status output. Bound the
credential write to five seconds on a daemon worker so a keyring prompt cannot
stall the campaign. `--prepare-only` stays secret-free, and resumed work uses
the existing keyring or environment override rather than generating a new
password.
For live progression, prefer one bounded multi-segment campaign process over
repeated one-shot connections. Before launching, verify no tester process is
already active. Omitted campaign `--reset-retries` now uses the `--segments`
budget so dynamic area depletion waits outside the area and retries instead of
silently converting an autonomous run into a blocked campaign; pass
`--reset-retries 0` only when an operator explicitly wants no reset wait.
On Windows, launch detached Python workers with `pythonw.exe` or an explicit
`CREATE_NO_WINDOW` creation flag, and redirect stdout and stderr to `runs/`.
Calling console `python.exe` directly can create a visible `conhost.exe` window
even when the worker is intended to run unattended.
When every fresh current-band source-ranked target is exhausted, the selector
may reuse a same-reboot route only if its evidence records a completed kill
and its policy XP delta is at least 50; this exception does not permit trivial
or crowded routes to loop, and ordinary absent/crowded cooldowns still defer
to the bounded reset controller.
From level 10 onward, an executable generic source-ranked candidate may lead an
ordinary fresh research probe; if no safe current-band candidate exists, keep
the named probe as the fallback. Never let generic ranking displace required
resource, training, quest, subclass, equipment, funding, flight, recovery, or
dedicated class/shared evidence transitions.
Live run 4661 validated this fallback for a level-10 mage: Aeloria killed the
Gnome Village treasurer and cook for 529 total XP, then returned to healer room
3054 at full health, mana, and movement.
When a generated multi-target circuit completes with no observed target, mark
every exact primary and supplementary policy saved in that circuit absent; do
not suppress unrelated reset rooms. If that generated absence is on cooldown
and the registered fallback most recently earned less than 50 XP, continue to
an independent generated candidate instead of alternating the two depleted
routes. Runs 4662-4664 exposed this Moria/Gnome oscillation at mage level 10.
Run 4665 validated the repaired rotation by selecting the independent
Fleshmonger kitchen circuit: Aeloria recovered her disarmed weapon, consumed a
verified cure-critical reserve at low health, killed both cooks for 715 XP,
and returned to healer room 3054 safely after the second kill.
Within that selector, fully source-safe current-band routes have priority over
special-procedure research; among safe routes, productive same-reboot evidence
comes first, then fresh routes, then retryable routes. Research remains
available after the safe progress pool is exhausted.

## Operational Fail-Fast Policy

Treat routine repository, test, live-run, source-refresh, and local process
operations as already authorized by the user. Use direct or previously approved
commands without asking for confirmation. Do not trigger a permission handoff
for an optional status or process audit; if that audit cannot run directly,
skip it and continue productive work. Never leave the task waiting for such an
audit.

Never wait, poll, or suspend useful work for an invisible permission review.
If an external action reports an approval timeout, retry that exact action once
immediately. If the retry also times out or fails, abandon the action for the
current pass, report it briefly, and continue with the best local or offline
work available. Retry the deferred action only after completing another useful
work unit or when the user explicitly requests it. Do not repeatedly poll for
approval, leave a required shell call hanging, or describe the task as blocked
while local implementation, testing, evidence analysis, or documentation can
still progress. A failed push or live connection must never prevent local
commits and verification.
For routine DD4 source refreshes and Git publication, do not request escalated
execution after an ordinary command times out. The app permission review can
delay command launch outside the command timeout itself; live run evidence on
2026-08-09 showed one such review consuming several hours. Give the ordinary
action one short attempt, defer it on failure, and continue local or live work.
Judge a live tester process by fresh SQLite events via `show-transcript` plus
its process state, never by the JSONL file's observed size alone. A temporarily
stale or zero-length file is not sufficient evidence of a stalled connection.
Never wait indefinitely on a live worker. If a socket or process produces no
transcript or SQLite progress for 45 seconds, allow one bounded reconnect; if
the retry is silent, close the exact worker, checkpoint or mark the segment,
and continue useful local work. Kill only the exact worker PID and never touch
the Discord streamer.
The CLI defaults every live `campaign` and `hero` segment to a 180-second
StarterBot cap plus a 60-second local setup budget and 45 seconds of cleanup
grace; keep that default unless a
bounded probe explicitly overrides it. A shell or app timeout must never be
the first cleanup mechanism. If an interrupted source-ranked worker is
reconciled without an objective kill, mark that exact reboot/level route as a
timeout hazard and rotate before launching another live connection.
When launching a bounded foreground segment, give the outer command timeout
more time than the segment's own runtime cap so the runner can recall, save,
and quit cleanly. The StarterBot deadline is a safe-return boundary: request it
once, trust either the local combat flag or a live GMCP enemy list, recall or
flee until combat is gone, recover at healer room 3054, then stand, save, and
quit. Cold source-catalog loading happens before the outer live-session timer.
The launcher uses a separate bounded local setup allowance, and its outer task
deadline only catches its own expiry; nested transport timeouts remain distinct.
The StarterBot clock itself starts at the beginning of the run and includes
local setup, and the cleanup phase has a 25-second hard limit. It must produce
a controlled checkpoint rather than leave a socket or process hanging.

For levels 71-75, the registered source-backed fallback is the Pirates Seas
Rastafarians probe/hunt. Source revision `bf745c3` identifies mobile 17099 in
room 17141 at source level 70, with no aggressive, sentinel, stay-area, or
special flag. Use `where rastafarians`, search only the registered reset room,
and require a fresh live `consider`: level difference determines XP-band
eligibility; HP wording remains a separate combat-risk signal.
For level 76, use the Ghost Town crypt thing probe/hunt; for levels 77-80,
use the Ghost Town retriever probe/hunt. Source revision `1b759f5` identifies
mobiles 8809 and 8829 as sentinel, stay-area, non-aggressive, and special-free
resets in rooms 8850 and 8843. Keep their closed-door routes and the adjacent
water-weird hazard behind the normal abort gates, and promote combat only
after a fresh exact `consider` proves the live level difference useful.

When an outbound official fastwalk sees a source-ranked target at an
intermediate waypoint, an opportunistic `consider` may collect evidence but
must not replace the official route with that later relative circuit stop. If
the target is below-band, crowded, or otherwise rejected, restore the
pre-intercept stop context, mark the outbound route complete at its actual
endpoint, and only then resume source-ranked stops. Keep this invariant
character-independent; the Moria run 5102 failure and the outbound-intercept
regression capture its need.

## Local Commit And Commentary Policy

Keep all changes local. Do not push, open pull requests, merge remote branches,
or otherwise publish to GitHub; the user handles remote publishing manually.
Attempt at most one local commit in each 24-hour period, scheduled for 9:00 PM
Pacific/Auckland time. Set a 60-second command timeout for that commit. If it
fails or times out, do not retry for 24 hours. Prefix every progress update to
the user with the current Pacific/Auckland local time so stalled work is
visible.
Beginning 2026-07-26, append every user steering message and every Codex
commentary or final response verbatim to `DEVELOPMENT_CONVERSATION.txt` in the
repository root. Stamp every entry using exactly
`[YYYY-MM-DD h:mm:ss AM/PM NZST] USER`,
`[YYYY-MM-DD h:mm:ss AM/PM NZST] CODEX COMMENTARY`, or
`[YYYY-MM-DD h:mm:ss AM/PM NZST] CODEX FINAL`. Do not substitute a speaker-first
header, UTC offset, ISO timestamp, or other format.
The `AM` or `PM` token is literal uppercase. In PowerShell, generate it with
`$stamp = (Get-Date -Format 'yyyy-MM-dd h:mm:ss tt').ToUpperInvariant()`;
do not use the locale's lowercase `am` or `pm` output. The Discord streamer
parses these append-only headers, so timestamp casing is a delivery contract.
Treat the file as append-only development history; do not rewrite or remove
earlier entries. Write an entry before or as the corresponding response is
sent so a stalled task cannot leave the visible discussion unrecorded.
The streamer configuration must include `USER`; after any logging repair,
confirm the source contains the user record, `streamer.stdout.log` contains
both `Publishing USER record` and a successful delivery with no matching
error, and the checkpoint offset equals the source length with an empty queue.
The streamer cannot infer a user message from the Codex interface. When a user
turn arrives, append that exact turn as `USER` before or with the response;
diagnosing Discord without checking the source file only hides the logging
failure.
Use `python tools/conversation_log.py append --speaker "CODEX COMMENTARY"
--body "..."` or `--body-file <UTF-8 text file>` for new entries whenever possible;
the helper emits the exact header and appends UTF-8 bytes without rewriting
legacy mixed-encoding history. It must reject a body containing another
timestamped speaker header; nested headers split one update into misleading
records. Before restarting or diagnosing the Discord
streamer, run `python tools/conversation_log.py validate`. A malformed
headerish line is a format failure to investigate, not a reason to change the
required header contract. Before every visible progress update, perform this
checklist: create the timestamped header, append the matching log entry, then
send the same header and commentary to the user.
Run the Discord streamer in permanent `--new-only` mode. This is a runtime
no-rewind guarantee, not merely a startup preference: if the conversation file
is truncated, replaced, or rewritten, discard queued and partial records and
checkpoint its new end. Never restart from byte zero or publish historical
records unless the user explicitly requests a one-off replay.
The streamer must keep `allow_historical_replay` set to `false` in its live
configuration, and `run_from_start_once.bat` must remain disabled. Even after
an explicit user request, historical replay requires both temporarily setting
that configuration value to literal `true` and supplying the separate
`--allow-historical-replay` command-line confirmation. Validate that a denied
`--reset-state --from-start` attempt leaves the existing checkpoint unchanged.
Maintain a monotonic local-record timestamp watermark in that mode, set to the
later of the source tail and the actual restart time. Reject the first record
at or before that cutover before queueing; after one live append crosses the
byte cursor, allow additional same-second records because they are still fresh
appends. Also reject a queued record older than the configured 30-second
live-feed age before sending it. These are independent backstops: cursor or
source-checkpoint damage must never become a historical Discord posting burst.
In `--new-only` mode, append position plus the monotonic local-record timestamp
watermark define newness. Seed a separate cutover content set from the source
tail and reject a copied pre-cutover speaker/body pair even when it is
restamped with a fresh timestamp. Apply this content fence only to `CODEX
COMMENTARY` and `CODEX FINAL`; never content-dedupe `USER` turns, because
repeated steering is a legitimate new turn. Include already-delivered Codex
content in the live fence as well, so a previously published assistant body
copied later cannot become a second Discord post. Keep exact-record
fingerprints to prevent the same append from being queued twice or replayed
after a checkpoint. Retry Discord HTTP 429 responses after their rate-limit delay, but
do not retry network failures or HTTP 5xx responses because Discord may have
accepted the request; mark that delivery uncertain and drop it to prefer
at-most-once posting over duplicate commentary. The 2026-08-14 repair verified
29 focused streamer tests, one live worker, an empty queue, and an EOF-matching
checkpoint after cutover. Launch the production worker directly with the
configured `python.exe` in `run_streamer.bat`; do not restore a `py.exe`
launcher/child pair, which makes cleanup and duplicate-worker detection
ambiguous. After any restart, inspect the fresh startup log for `Initial mode:
new records only` and no historical `Publishing` lines before accepting new
traffic.

## Commits And Pull Requests

Use concise imperative commit subjects, for example `Persist character state
snapshots`. Include verification details and behavioral impact in pull
requests. Follow the local commit schedule above and leave remote publishing to
the user. Never stage generated run data, transcripts, secrets, or unrelated
user changes.
