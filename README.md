# dd-playtester

An experimental autonomous Dragons Domain IV playtester using asyncio Telnet,
GMCP, source-backed deterministic policies, and durable run evidence.

**HERO 100 is not yet demonstrated.** Creation, tutorial play, reporting, and
resumable campaigns work. The highest roster level is 25; the fresh-creation
track is 8. See the [current review](docs/APPROACH_REVIEW_2026-09-08.md) for
measured results and the [roadmap](ROADMAP.md) for remaining acceptance gates.

The current live frontier is Kestrel, level 24 at **331,264 XP**, with durable
checkpoint **41370** in healer room **3054**, GMCP alignment **1000**, and fame
**-12**. Run 13235 executed the source-ranked Moria route and acquired a purple
sanctuary potion. Runs 13236-13256 recorded bounded route, fame, provision, and
flight-funding outcomes; the Green Dragon attempt in 13256 observed **576 HP**
against the previous **342-point** conservative output ceiling, withdrew after
gas nausea, and lost **385 XP** without a kill or fame change. Runs 13257-13258
completed safe Crystal food-reserve routes and acquired one grain reserve. The
campaign preserves the negative-fame ticket refusal, the Green loss, and the
current-reboot sanctuary cooldown; it does not replay those closed policies.
Policy revision 301 also fixes the Green improved-output retry so its protected
sanctuary opener reaches the live stop builder when a future reboot and reserve
make that one-shot retry eligible. The next live gate is therefore a newly
source-supported sanctuary or fame route. A fresh `quest request` is not a
negative-fame escape: DD4 rejects it below zero fame, and the campaign also
refuses to request when live fame is unknown. An already active quest may still
be completed.
Astrevo remains level 8 at checkpoint 40956. Sustained
progression and HERO proof remain open.

The parser now mirrors the refreshed DD4 source's three weighted mobile-special
slots, area `#SPECIALS` `M`/`N`/`P` overrides, and explicit `AFF_MINDLESS` flag.
Existing live checkpoints retain their recorded source revision until resumed.

The current campaign policy revision is 301. It preserves the source and live
GMCP gates while allowing a nominally current-level passive target whose DD4
load-time HP fuzz reaches two levels above the character to receive one
sanctuary-protected damage-window probe. This is a measured admission path,
not a general level or safety override. It also lets reachable direct ground
gear resets improve combat output before the campaign attempts flight funding
or a carrier fight. For the exact source-famous Green Dragon gas contract,
sanctuary plus healer nausea recovery can extend the live probe to the existing
finite 36-action horizon after sanctuary is observed; the ordinary source
estimate remains twelve actions and is unchanged before that point.

`show-combat-readiness` reports alignment and fame separately, along with the
current quest status, questmaster route, quest-point level gate, and the
source-backed fame outcome. Only a completed kill quest awards positive fuzzy
fame; object, retrieve, and hoard quests award quest points or gold but no
fame. A negative-fame character therefore needs a proven gear/output route or
an eligible fame-awarding kill, not a guessed quest request.

The fame-recovery policy mirrors the `ACT_IS_FAMOUS` fame branch in `fight.c`. For
Kestrel's negative-fame recovery, the offline selector now identifies Green
Dragon mobile 6112 as a one-shot candidate only with sanctuary, the exact
source route and HP budget, and healer mobile 3012's source-proven
`spec_cast_adept` recovery for gas-breath nausea. This is an offline policy
authorization for a bounded live probe; no Green Dragon kill, fame recovery,
or HERO progress is claimed yet.

The `--autonomous` supervisor now counts one completed reset wait rather than
each progress heartbeat and preserves every bounded result in SQLite.
His source-verified long slim dagger (vnum 5252) gives a
318-point conservative opener-plus-repeat ceiling. The refreshed source is
`80cad01` (full revision `80cad011b8c17b5ffc8828edae9182271bf7e46e`). Readiness finds
317 source-band candidates, 93 autonomous-safe candidates, 1,154
output-fitting candidates, and protected HP probes under the revision-301
nominal-current-level admission. The newly selected Shudde-M'ell route still
requires live GMCP confirmation and may withdraw without combat. Runs 13093 and
13100 proved both permitted
Moria carrier instances and acquired two purple sanctuary potions for 180
maintenance XP without dying. Run 13117 reached Chaplain Jerrold at 416 HP and
withdrew before a losing exchange against the 318-point ceiling. Astrevo's
latest checkpoint is 40956; runs 13179 and 13181 added 180 and 118 XP from
source-ranked current-band routes. Runs 13180, 13182, and 13184 recorded
bounded target-absence or crowd outcomes, while runs 13183 and 13185 kept the
finite provision-funding boundary explicit. Run 13185 also recorded an exact
source sentinel one room before its registered reset room; the interception
now resumes that already-vetted outbound step after a temporary crowd instead
of recalling before the reset endpoint is checked. Run 13186 exercised that
one-shot campaign revalidation live: the endpoint was checked, a new
two-mobile crowd closed the marker, and Astrevo returned safely to healer room
3054 without XP change. Runs 13190-13192 then exercised overweight sack
recovery, coin banking, route rotation, and interrupted-worker recovery; the
latest boundary remains safe at healer room 3054 with no new loss. Run 13125
added 40 below-band maintenance XP and a 50-copper
Midget coin drop; runs 13126-13127 completed Circus and Mirror Realm fame
recovery checks with no XP change. Run 13132 completed a patrolling-guard
funding attempt for 90 below-band maintenance XP and 1 copper. Run 13133
acquired the second purple reserve for 100 maintenance XP; runs 13134-13135
recorded bounded fame-route boundaries without XP change. Run 13136 added 110
maintenance XP and 1 copper against the on-duty guard, after which the selector
correctly reopened Moria sanctuary recovery. No sustained HERO progression or
HERO proof is claimed.

Run 12985 refreshed source-verified food and the DD4 source revision. Run
12986 used the exact source-ranked `where drunk` locator to reach the Solace
Secretary route, then withdrew before combat because the loaded target's
source HP ceiling exceeded Kestrel's fixed knife-toss budget. Checkpoint 40039
preserves that evidence and the one same-reboot loss record, so the chooser
will not repeat the probe until a fresh legal route is available.

Campaign startup reuses a current-level, current-reboot live training audit
when one is present, avoiding a large historical event scan in the shared
SQLite database. Legacy checkpoints still receive historical skill backfill;
the public runner reports each preparation boundary and stops within its
bounded setup allowance.

## Setup

Run from the repository root with Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
python -m dd4tester --help
```

Leave the environment with `deactivate`. Without activation, replace `python`
with `.\.venv\Scripts\python.exe` in these examples.

## Create Or Resume

```powershell
python -m dd4tester hero-options
python -m dd4tester hero --race human --sex female --class mage --prepare-only
python -m dd4tester hero --race human --sex female --class mage --progress
python -m dd4tester hero --race human --sex female --class mage `
  --autonomous --progress
python -m dd4tester hero --username Astrevo --workspace runs/heroes/astrevo `
  --segments 3 --max-segment-runtime 180 --reset-retries 1 --reset-wait 180 --progress
```

`hero-options` lists source-legal identities. Requests accept race, cosmetic sex,
base class, optional level-30 subclass target, name, and personality. Omitting
the name generates a stable name. `--prepare-only` writes configuration without
connecting; repeat the same request/workspace to resume. Names select history,
never special gameplay behavior.

```powershell
python -m dd4tester hero --name Newmage --race human --class mage `
  --personality "patient, observant, and dryly funny" --prepare-only
python -m dd4tester hero --username Existingthief --race drow --class thief `
  --subclass ninja --password PLACEHOLDER --target-level 30 --prepare-only
```

Remove `--prepare-only` to execute. `--username` aliases `--name`.
`--target-level` accepts 2-100, default 100. A resumed target can be extended,
not lowered; use a separate workspace for a shorter validation horizon.
`--new` starts a new stored campaign, not a second identity in the MUD.

`hero` is a bounded invocation. Add `--autonomous` to keep opening one
bounded worker at a time until the target is reached or the campaign reports a
durable blocker. In this mode `--segments` is the cycle budget and
`--max-reset-waits` (default 3) is the total area-reset wait budget. The
supervisor preserves the same SQLite checkpoints and credentials between
cycles, counts one completed wait rather than each progress heartbeat, returns
on a real failure or blocked policy, and never spins on an unchanged world. A
returned `ready` result is safe to resume later.

### Credentials

New executed HERO requests generate and store their password in Windows
Credential Manager. Named resumes reuse `character:<name>`. `--password` or
the matching environment variable overrides it; `--remember-password`
explicitly saves that override for later resumes.

Plaintext arguments can appear in shell history and process listings. Prefer
stored credentials for unattended runs. Passwords are redacted from transcripts
and never written into generated profiles, requests, reports, or SQLite.

```powershell
python -m dd4tester configure-login
python -m dd4tester configure-character-password profiles/your-character.yaml
```

The first configures scenario login; the second configures a profile credential.
`DD4_USERNAME`, `DD4_PASSWORD`, and profile password environment variables remain
supported.

### Bounds And Recovery

`--segments` limits checkpoint segments. The public `hero` command defaults to
`--max-segment-runtime 180`, so every live worker has a bounded field and
healer-return window while the process continues through durable checkpoints.
The Python `run_hero_request` entry point uses the same 180-second default and
normalizes a missing cap to it, so library callers receive the same liveness
contract.
An explicit `--max-segment-runtime 180` on `campaign` enables the same short
continuation and defaults reset retries to zero. Add
`--reset-retries 1 --reset-wait 180` for one wait outside a depleted area.
For either command, omitting the runtime override retains the command's
default; longer values are explicit bounded probes, not an unbounded mode.
Live cleanup has its own allowance.

For unattended progression, use `hero --autonomous --progress`. Its worker
and reset budgets are finite by design; increase them explicitly only when
the surrounding run supervisor can observe and stop the process.

Use at least two segments when a reset wait may need a world-time probe before
field selection. The probe consumes a segment. A fresh response confirming the
same reboot after the completed wait permits reselection; an area reset does
not require a reboot. Missing observations and ordinary loss, route, resource,
and protection gates still block execution. `--retry-stalled` permits one bounded
frontier rotation, not a safety override. For a level-10-through-29 thief whose
current-band output-fitting frontier is empty, it may also open one exact
source-audited Forest bear-claw maintenance attempt. That exception requires
the healer checkpoint, food, water, movement, weight, protection, route, and
live gates; it records boot, level, and source revision before connecting and
closes after the attempt. It is not an XP or below-band permission.

The normal attempt limit still ends the invocation even when reset retries
remain. A funding-exhausted `ready` result can represent an area-reset wait;
read its message as well as its status. A new bounded invocation can use its
own explicit retry budget; do not run duplicate workers.

Resume also reconciles losses first observed after a disconnect. A verified
same-level XP decrease sets a lower bound on `campaign_xp_loss_total`, even
without a captured penalty message. This does not invent a death or identify
the command that caused the loss. Replaying saved history cannot charge the
same decrease twice; explicit larger loss counters remain authoritative.

For wandering hunt targets and funding carriers, the runner can stop the approach at a verified
waypoint in the same area and locate the target before visiting its reset
room. Fresh results choose a source-checked route; uncertain approaches keep
the original plan. This saves travel without adding searches or retry budgets.
Ordinary hunts retain any required familiar staging waypoint before locating
the target. Specialised transit-recovery plans, closed or random approaches,
and routes whose required preflight would be omitted keep the original route.
If a below-band wanderer is intercepted before the planned destination, the
runner retains its exact route position and continues the unvisited path.
It does not jump to the following leg as though it had reached the endpoint.
Later targets still need fresh consideration; no search or retry budget grows.
An intercepted room check retains control after a bystander response. The
remaining exact target must receive its own consider before travel or attack;
an inconclusive check cannot silently resume the outbound route. This handoff
is replay-tested, with fresh live acceptance still pending.
A uniquely source-identified sentinel seen beside its planned reset room can
also be considered on approach. This requires a fresh exact instance and
matching source/live room exits; normal crowd, combat, and loss gates remain.
Run 13186 live-validated the navigation handoff once. A pending marker can
open only that exact source-ranked segment through the outer crowd wait; the
segment consumes the marker and a new crowd closes it without granting combat
permission or XP credit.
Restricted protection-carrier trips can query the exact source identity before
their final approach, then search accessible source-mapped rooms. The bounded
plan retains excluded locations as sightings rather than reporting area absence;
it does not grant access to hazardous deep routes or bypass combat checks.
The deep-reserve fallback can use this same search from level 16 when
invisibility is source-authorized and positively practiced. A fresh live effect
is still required. Lower-level or unqualified characters retain the restricted
reset-room plan; the change does not grant a new retry or reduce required loot.
When an exactly identified carrier shares its room with one ordinary bystander,
the runner uses its existing bystander consideration and bounded crowd waits.
Only fresh evidence can discount that bystander; the carrier still requires
its own normal combat checks. Dangerous or unidentified crowds remain blocked.
An absent carrier in a fully source-identified passive room can use the normal
search continuation to the next already-planned endpoint. This is not combat
permission, and it adds neither locator queries nor route alternatives.
On resume, checkpoint cleanup does not treat an inherited field-abort message
as a fresh funding failure. A completed, safely returned carrier run can repair
that exact replayed restriction; newer failures and other route hazards remain.

Positive, source-tagged funding kills also update their exact hunting-route
reward evidence. Their runs remain funding segments, and XP is not counted
twice. A fed character may prefer an executable ground hunt when the latest
same-reboot carrier sale cannot cover the observed flight-price shortfall.
Food, protection, loss, and retry requirements still apply; this preference
does not authorize another loan or an extra trip for missing protection.
Below-band kills selected specifically for provision funding are retained in
`completed_kills` even when they are absent from `objective_kills`; successful
funding advances its retry cooldown without becoming progression proof.

If an identified familiar finishes the pending target before the player can
attack, the runner records a zero-XP encounter, cancels that player opener,
and preserves corpse looting. Source-ranked low-load targets whose audited
player damage budget already covers their HP ceiling now withdraw the familiar
after its opening probe so the player receives the kill credit. This remains
maintenance evidence until player XP is observed in the transcript; ordinary
progression must still be earned from the live player kill. The opening-death
fix is replay-verified.

Familiar preparation waits for its own summon, room-listing, and grouping
acknowledgements within one 30-second deadline. Unrelated world messages do not
trigger a duplicate cast or immediate recall. Temporary confirmation failures
retain the normal bounded retry; explicit refusals and identity failures do not.

A freshly considered easy-kill load may instead use a source-budgeted solo
fight. The runner first confirms that its owned companion is asleep, then
uses the existing timed encounter and measured-damage checks without companion
damage credit. It confirms the companion is awake before ordinary onward
travel. Each acknowledgement is capped at five seconds; an uncertain handoff
returns to recovery. Stronger or underfunded targets keep the normal familiar
path. No new CLI option is required. This does not yet avoid summoning costs.
Solo continuation uses the opponent's remaining health, current spell costs,
observed damage rate, and the original time/command limits. A single missed
spell or narrowly missed opening-damage threshold is not itself a retreat.
The live sleep/opening sequence is confirmed; a complete solo kill/wake cycle
with this continuation correction still needs live acceptance.

For a source-ranked target whose audited player output already covers the
target HP ceiling, the familiar may make one bounded probe attack, then the
runner confirms its withdrawal before opening player combat. For DD4's charmed
pony this uses the source-recognized `order <familiar> flee Fear` override and
requires the positive in-place sleep message; ordinary familiars require the
actual departure message. This
prevents a familiar's next round from taking the finishing blow. Run 13053
live-proved the sequence against Granny Jenkins: Astrevo personally received
168 objective XP and returned safely.
If the familiar cannot be positively withdrawn within its bounded attempts, the
runner abandons the stop and returns through the healer path; it must never
fall through to a player opener after that failure.

Fixed fame routes use the same source-backed player output envelope as the
dynamic frontier. Their live damage-window probe compares measured target and
player HP against the current action budget; a target that cannot be completed
inside that budget is abandoned before protection expires. GMCP target level
and HP remain authoritative, while source estimates only admit or bound the
probe.

A roaming city obstruction can trigger up to three 12-second healer waits
within a shop segment, each followed by a fresh location check. Persistent
obstruction normally stops travel. Invisibility requires source authorization,
positive observed practice, sufficient mana, and an awake noncombat state;
class and level alone do not authorize a cast.

For source-audited field routes, fresh active invisibility can also suppress
an ordinary sight-dependent greeting hazard. This does not bypass detecting
mobiles, all-greeting programs, unrelated hazards, or combat checks. Expiry,
an explicit invisibility-loss message, or reconnection revokes the exemption;
saved effects alone never grant it. Route messages distinguish the observation
room from the reported mobile location. No additional CLI option is needed.

Required-loot carrier searches can use the same source-proven visibility rule
for ordinary aggressive transit mobiles. The character must have an audited
class path, positive observed `invis` practice, and a live effect that the
runner maintains while moving. Detect-invisibility, scripts, equipped reset
objects, pre-combat specials, and unknown behavior remain hard exclusions.
This may inspect up to 12 rooms within the existing 24-step circuit; target,
consider, crowd, resource, and return-home gates are unchanged.
Because `where` reports display labels rather than room VNUMs, a bounded plan
preserves coverage for distinct labels before adding duplicate names. A field
`look` completes only after an actual room listing. Unrelated status output is
ignored; silence receives one five-second retry and then a safe abort. An empty
locator path never rechecks a room already proved empty.

An ordinary aggressive transit mobile with a combat-only special follows the
same source aggression cutoff as its normal attack. The route remains blocked
when the highest fuzzed mobile level is within ten levels of the character;
only a strictly larger gap makes that special inert before combat. Pre-combat,
economic, scripted, equipped, unknown, engaged, and endpoint hazards remain
blocked. This rule can widen an existing bounded locator circuit, but it adds no
room, step, query, retry, combat, or resource permission.

When a city obstruction is recorded, the existing world-time probe also makes
one observation-only `where drunk` check at the healer. A fresh off-route
location may release that route cooldown, but not an actual purchase failure.
The next shop trip still performs its own preflight. No extra wait or segment
is added, and the probe never buys, borrows, or travels to a shop.

Flight shopping may instead admit the existing source-bounded city greeter risk
when the character is ready. This allows one isolated, exactly identified weak
interruption, with a 70% health floor and 60-second combat deadline. Extra or
unidentified enemies, changed source bounds, or the segment deadline force
withdrawal. A failed attempt remains excluded at the same level/reboot; missing
reboot evidence never grants a retry. Purchase failures and loan limits remain.
The audit is stored as `campaign_city_shop_transit`; timers are connection-local.

Source-backed field departures also check the actual Midgaard route and fountain
when guard assistance cannot be ruled out by revealed alignment. This shares
the bounded city locator/wait behavior; it adds no retries to the campaign.
`campaign_field_city_preflight` records the result separately from shopping.
DD4 sends the actual alignment through `Char.Worth` at level 10 and above,
clamped by the server to -1000..1000. Below level 10 it intentionally sends
50000 as a concealment sentinel. The parser retains the wire value in state and
transcripts; policy derives only a level-aware, in-range value. `spec_guard`
uses 300 as its own assistance cutoff, while `violence_update` separately
requires both a good bystander and a good player at the exact 350 threshold to
suppress its generic assist. A target NPC's alignment is not a substitute for
the player's value. Raw packets remain unchanged in transcripts.
A confirmed healer-origin departure deferral stops the current invocation after
its existing short waits. It consumes the segment but not a funding-target or
hunting-endpoint attempt. The checkpoint reason is
`field_city_departure_blocked`. A later invocation with the same level and
reboot blocks the recorded policy when its exact policy ID is present; a
different source-ranked route gets its own bounded preflight. Legacy
checkpoints without a policy ID remain conservative and require fresh
`time`/route evidence, so repeated calls cannot burn identical city checks.

A below-band target is still skipped for XP. If it has already attacked at its
registered endpoint, one exactly identified ordinary enemy may use the existing
30-second combat-finishing budget instead of an automatic XP-losing retreat.
Source hazards, fresh health/mana, nutrition, extra attackers, and command
acknowledgements still govern continuation. Its kill is incidental, never a
repeatable XP objective. Inspect `campaign_fastwalk_encounter_budgets` for the
`below-band-endpoint-defense` audit; no new CLI option is required.

Source-ranked routes also carry an explicit source VNUM for at most one
borderline transit aggressor when source damage bounds prove the reset safe.
The live runner may finish that exact mobile once if GMCP confirms an isolated
below-band instance and the ordinary health, nutrition, consider, and combat
gates pass. The result is recorded as maintenance and cannot become an XP
target; unregistered attackers and useful-band rolls still cause withdrawal.

Run only one gameplay worker at a time. After an interrupted worker has stopped:

```powershell
python -m dd4tester return-home profiles/your-character.yaml
python -m dd4tester resupply profiles/your-character.yaml
python -m dd4tester restock profiles/your-character.yaml
```

Recovery belongs at Midgaard healer room 3054. Never quit in Purgatory.
See [operating instructions](docs/OPERATIONS.md) for timeout and process rules.

## Inspect Progress

Replace these examples with IDs printed by your run:

```powershell
python -m dd4tester show-runs --limit 20
python -m dd4tester show-transcript 12767
python -m dd4tester show-state 12767 --history
python -m dd4tester show-campaign 7
python -m dd4tester report 12767
python -m dd4tester campaign-report 7
python -m dd4tester report 12767 --format json --output reports/run-12767.json
python -m dd4tester show-combat-readiness --level 24 --class thief `
  --character Kestrel --all-areas
```

Reports distinguish XP, kills, losses, deaths, decisions, and recovery. Non-secret
title, description, and personality remain in run context. Commentary derives
from stored events; a report does not itself prove autonomous HERO progression.
The parser now reconciles DD4's LF-CR flee/refund lines with GMCP without
subtracting the same loss twice. Historical records are not rewritten:
run 12816's raw GMCP confirms 28,815 XP (net -53), while checkpoint 39419
incorrectly retains 28,747. Fresh recovery run 12820 confirmed 28,815 and the
normal public resume saved it in checkpoint 39433. This correction is not
earned XP; the genuine loss and original audit records remain relevant.
For multi-stop source hunts, the circuit name is not the killed target's
identity. Reconnect reconstruction uses each kill's source policy ID and keeps
later stop-specific failures distinct from that earlier success.

Crowded field rooms can receive up to three exact-instance consider probes per
visit. Only positively identified below-band bystanders are discounted; a
remaining XP target still needs its own ordinary consider and combat checks.
Follow-up attacks retain the selected instance rather than switching to a
same-name bystander. These probes are recorded under
`campaign_fastwalk_bystander_consider_outcomes`, not restored as permissions.

An ordinary source-ranked hunt may also admit one exact, distinct room
bystander when its stop explicitly opts in. The primary target and bystander
must be source-identified, unarmed, ordinary, non-aggressive, non-scripted,
non-special mobiles with fresh exact selectors and easy-kill considers. A
source-estimated two-mobile HP, incoming-damage, mana, and six-action budget
must fit at near-full health. Any extra, unknown, armed, scripted, special, or
scope-changed mobile withdraws the fight. The result is audited in
`campaign_fastwalk_encounter_budgets`; it is regression-tested, but live
acceptance and any XP claim still require a fresh DD4 run.

## Data Locations

Defaults when running from `E:\dd-playtester`:

| Artifact | Location |
| --- | --- |
| SQLite | `E:\dd-playtester\runs\dd4tester.sqlite3` |
| JSONL transcripts | `E:\dd-playtester\transcripts\<scenario-name>-<run-id>.jsonl` |
| HERO request/profile/campaign | `E:\dd-playtester\runs\heroes\<workspace>\` |
| Target-completion reports | `runs/heroes/<workspace>/hero-report.json` and `hero-report.md` |
| Development conversation | `E:\dd-playtester\DEVELOPMENT_CONVERSATION.txt` |

Relative locations resolve from the working directory; profiles/scenarios can
configure other destinations. Run records retain the actual transcript path.

SQLite tables: `runs`, `events`, `state_snapshots`, `character_commands`,
`character_acquired_items`, `character_item_backfills`, `loot_sales`, `mob_kills`,
`campaigns`, `campaign_segments`, `campaign_checkpoints`, and `campaign_usage`.
`mob_kills.route_gate` marks an incidental source route-gate kill; it is not
progression evidence even when the kill produced experience.

`loot_sales.sold_coins` and campaign funding `proceeds` are gross shop prices,
not necessarily carried income. Shops divert part of a sale toward outstanding
bank debt; use the live currency snapshots and loan notice to reconcile cash.

```powershell
python -m dd4tester show-transcript transcripts/login-1.jsonl --raw
python -m dd4tester campaign-report 7 --format json --output reports/campaign-7.json
```

## Scenarios And Source Analysis

```powershell
python -m dd4tester run scenarios/login.yaml
python -m dd4tester run scenarios/capture.yaml
python -m dd4tester starter profiles/starter.example.yaml
python -m dd4tester campaign campaigns/hero.example.yaml
python -m dd4tester show-policies --class mage --level 8
python -m dd4tester skill-analysis --class warrior
python -m dd4tester show-prereqs --class mage --skill fireball
python -m dd4tester show-gear-sources --level 24 --class thief `
  --stance combat --all-areas
python -m dd4tester show-combat-readiness --level 24 --class thief `
  --character Kestrel --all-areas
python -m dd4tester autonomy-audit --race human --sex female --all-classes --target-level 100
```

The capture scenario connects to `dragons-domain.org:8888`, observes room and
character output, and quits. Configure credentials first. Static audits describe
registered templates, not live executable coverage. Observed skill names require
source authorization and positive practice before execution.

`hero --source` accepts the DD4 source/area directory or `const.c`. Workspaces
retain the resolved directory and source evidence. Keep the local DD4 checkout
fresh and review changes before live use. Race/class validation is declared in
`matrices/level-10-all-race-class.yaml`; the existing roster is in
`matrices/active-hero-rotation.yaml`. Run serially and use `matrix-coverage` to
distinguish declared entries from actual proof.

`show-gear-sources` ranks source-reset equipment for a requested class and
stance (`combat`, `pre_level`, or `recovery`). It includes equipped and carried
mobile drops, shop stock, ground resets, source level ranges, route origins,
exact source keywords, hazards, autonomy rejections, and a `weapon_role`
column. Thieves automatically receive the source-backed `piercing` primary
preference used by the backstab planner; stronger non-piercing weapons are
shown as mismatches rather than upgrades. Use `--database` and `--character`
to compare the latest stored loadout. This is acquisition evidence only: a
promising row does not authorize combat or claim live availability. Campaign
execution additionally requires an exact source-ranked carrier hunt when the
item is mob-carried or mob-equipped, including one source spawn, clean route
and hazard gates, a fitting live HP budget, and an exact post-kill loot/equip
step. Source class-slot coverage and live carrier acquisition remain active
proof gaps.

`show-combat-readiness` is a read-only checkpoint and source audit. It reports
the learned repeatable action, conservative damage ceiling, durable campaign
constraints, separate player alignment and fame, ranked current-band targets,
and stronger gear placements with their source rejection reasons. Use `--json`
for automation. Its output is
analysis only and never authorizes a live connection; a target still needs
the campaign's fresh consider, protection, resource, route, and loss gates.
The source report also exposes each target's resolved `MobDamMod`; this is the
per-attack NPC damage scalar from the pinned DD4 source, applied before
sanctuary and critical-hit bounds. An unknown scalar rejects the target rather
than silently treating it as neutral.

## Mudlet Visibility

```powershell
python -m dd4tester mudlet-bridge --directory runs/mudlet-bridge
python -m dd4tester hero --race human --sex female --class mage `
  --transport mudlet --mudlet-directory runs/mudlet-bridge
```

Import the bridge into the DD4 Mudlet profile and share its directory with the
Windows VM. See [the bridge guide](docs/mudlet-bridge.md). Telnet remains primary;
automated VM lifecycle and full visible HERO proof are unfinished gates.

## Development

Some source-integration tests require the public DD4 checkout. Once per clone:

```powershell
git clone https://github.com/fromage-fraser/dd4.git runs/dd4-source
```

Keep an existing checkout fresh with `git -C runs/dd4-source pull --ff-only`.

```powershell
python -m pytest -q
python -m pytest -q tests/test_damage_window_timing.py
python -m compileall -q dd4tester tests
```

Latest full offline verification: **5,756 tests pass**. The dedicated CLI
regression suite passes **69 tests**. Reconnect accounting
preserves verified XP decreases first observed after disconnection, without
double-counting or inventing their cause. Campaign startup now preserves
campaign-owned potion and source-resource ledgers when a raw live snapshot
omits those fields. Fresh source combat-budget evidence can reopen a previously
cleared Forest upgrade without erasing its crowd quarantine. Run 12984 recorded
that retry and withdrew at room 18027; the earlier checkpoint 40031 recorded
Kestrel at level 24 and 332,692 XP in healer room 3054. The latest focused Moria and locator
regressions also pass; the nine-endpoint fallback remains within the shared
24-step movement bound.

Run 13106 reached the source-validated Forest crowd gate and exposed a runner
acknowledgement bug: recall was sent from room 18027, but a lagging text-room
cursor made the policy report failure before the server response arrived. The
state-aware acknowledgement fix passed the full suite and live run 13107;
Kestrel received the Temple Of Midgaard response, recovered at healer 3054,
saved, and quit cleanly. The latest checkpoint is 40551 at level 24 and
331,521 XP; no progression XP is claimed by this recovery segment.

Run 12880 live-validated Aeloria's invisible carrier-search handoff, reaching
both carriers together, but duplicate-target handling prevented consideration.
Run 12881 then exercised the fix live: exact-instance consideration selected a
large hobgoblin, Aeloria gained 90 XP, ate its severed head, and returned full
to healer 3054. Run 12882 found the White Stag absent and returned safely with
no loss. Aeloria is now level 18 at 161,181 XP. This is the first positive
post-fix kill, not yet sustained progression or HERO. The
[contributor guide](AGENTS.md) defines coding, evidence, and local-only commit
rules. The [preserved README](docs/history/README_2026-09-08.md) retains earlier
details and run history; superseded defaults there are not the current
operating contract.

### Current Frontier: Kestrel (September 10, 2026)

Runs 12948-12953 followed the level-24 source frontier. The secretary target
exceeded the dagger damage budget, the Forest bear-claw route reached room
18027 and correctly withdrew from a live crowd, and the flight shop refused
service because fame is -12. Run 12959 then completed a below-band Midget
funding kill for 40 XP and 50 copper. Run 12960 cleared the recovered purse,
12961 sold its loot for a 2,878 copper-equivalent balance, and 12962 found the
watchman research route viable. Runs 12963-12965 safely exhausted the current
Moria sanctuary attempts. Reconnect run 12966 was interrupted and repaired;
runs 12967-12970 completed bounded food and recovery maintenance. Run 12971
used the widened nine-endpoint Moria fallback, killed source carrier 4055 for
100 below-band XP, and stored purple potion 4050 in the pouch. Runs 12972-12978
continued food and target probes safely. Run 12979 proved the pouch ledger is
preserved across a new live connection; run 12981 replenished food, while runs
12980 and 12982 reached current frontier targets and rejected them on source
damage bounds. Run 12984 reopened the Forest upgrade only after fresh source
damage evidence, reached room 18027, and withdrew when source-registered
mosquito and wasp instances formed a crowd. Run 12985 refreshed source-verified
food and the current DD4 source revision. Run 12986 reached the Solace
Secretary route through the exact `where drunk` locator, then withdrew before
combat because the loaded target's source HP ceiling exceeded the fixed
knife-toss budget. Run 13016 then completed the corrected sanctuary-reserve
handoff. Run 13018 reached the source Cyclops in Elemental Canyon. GMCP
reported 407 maximum HP, above the 318-point source combat budget, but the old
endpoint path still opened after sanctuary and withdrew only after the
aggressive target and an unapproved attacker were active; the net loss was
338 XP. The loss and live target evidence are retained, and the fixed endpoint
now passes the exact validated enemy records into the budget gate. Kestrel is
level 24 at 332,289 XP at checkpoint 40172, safely in healer room 3054. HERO
remains unproved.

The source-ranked chooser now requires a legal live HP probe whenever a plain
target's source HP range crosses the character ceiling. A current-band target
may use one sanctuary-protected GMCP damage-window probe only when its lower
HP bound fits the audited player output and its route passes the established
source locator contract. For a source-identified passive target, the live
runner may issue exact `consider`, consume sanctuary, and open combat before
the first `Char.Enemies` HP record exists; scripted, special, armed, and
uncertain targets remain excluded. The live ceiling still has to fit the fixed
source damage budget; no source estimate grants an unlimited fight.

When a same-level source target has one recorded HP-budget loss, a strictly
stronger audited loadout may reopen that exact mobile and room once. The retry
requires matching reboot, source revision, policy identity, observed GMCP HP,
and current-band route gates; the marker is consumed when the live segment
starts. A changed weapon cannot reopen a different target or turn an
over-budget target into general permission.

Use the source checkout refresh command above before source-sensitive planning;
do not treat a live observation or static source estimate as proof of a kill.
The current source mirror is up to date at `622d5de`, the affected campaign
suite passes **1,464 tests**, and offline selection still finds no Kestrel
target that passes all three filters at level 24. Live progression remains
unproved.

### Alignment Evidence Correction: September 11, 2026

The upstream source confirms that `Char.Worth.alignment` is accurate at level
10 and above; level 1-9 uses the deliberate wire mask `50000`. Live run
13036 captured alignment `1000` for Kestrel at level 24, so the transport was
not corrupt. The policy gate had instead applied the NPC target's alignment to
DD4's player-fight assistance rule. It now uses the player's revealed value:
`violence_update` blocks a good bystander only when both sides meet the exact
350 `IS_GOOD` threshold, while `spec_guard`'s separate assistance path uses
the 300 threshold. The raw GMCP value remains preserved for evidence, and
masked or invalid values fail closed.

### Cross-Class Continuation: September 11, 2026

The warrior Dorrik completed bounded flight preparation, then rotated through
the Sentinel and Abyss routes; both source-valid targets were absent and he
returned safely to healer room 3054. Serevian's thief weapon-repair route
completed without acquiring the missing bear claws after an unrelated field
combat caused a safe return. Astrevo's mage then killed the Circus Bearded
Lady for **140 XP**, survived, and checkpointed at level 8. That live run
exposed a classification error in which the source-defined hairy key was
treated as combat gear. Keys are now excluded from stance selection and are
removed if already worn; pouches remain supported. The next live gate is a
productive repeat for Astrevo or Serevian, followed by a level transition.
Astrevo's next New Ofcol attempt found a source-observed crowd at Gallow Hill
and withdrew without combat or loss, preserving the earlier XP gain.
Offline source work now exposes the legal infernalist `hellfire` and witch
`wither` damage paths through the shared estimator and timed spell contract;
this is executable coverage, not live subclass or HERO proof.

### Latest Live Evidence: Sanctuary Reserve Repair (September 11, 2026)

Policy revision 273 repaired a markerless checkpoint left by the previous
second-reserve handoff. Live run **13016** selected the corrected
`source-ranked-sanctuary-recovery-2-100` policy, reached source mobile 4055 in
Moria, and used the exact live target ID after a below-band `consider` result.
The kill was admitted only because one sanctuary reserve was missing: it
provided 110 XP and the second purple potion, which was placed in the pouch.
The character did not quaff either reserve, returned to healer room 3054,
slept, saved, and quit safely. Segment **12566** and checkpoint **40159** record
level 24, **332,627 XP**, two verified purple reserves, and no new death or XP
loss. This is recovery and source-required-loot evidence, not sustained
progression. The campaign tests pass **1,421**, the affected cross-module tests
pass **1,766**, and the full offline suite passes **5,515**; HERO remains
unproved.

### Latest Live Evidence: GMCP HP Budget Gate (September 11, 2026)

Run **13018** selected the exact source-ranked Cyclops revalidation at level 24.
GMCP identified mobile **9202** at **407/407 HP**, while the source-audited
thief output budget was **318 HP**. The run withdrew after the aggressive target
engaged and produced a net **-338 XP** result, with no death or kill; checkpoint
**40172** is safely at healer room **3054** with **332,289 XP**. The loss remains
in the current-reboot ledger and the target is closed for this level. The
endpoint implementation now passes its already-validated live enemy records
directly to the HP-budget check, and regression coverage protects that ordering.
The endpoint regression remains covered; the latest affected campaign,
starter, and progression suite passes **3,341 tests**. The full offline result
above predates the two newest regression cases.

### Latest Frontier Selection: Protected Level Ceiling (September 11, 2026)

The source-ranked selector now exposes Mr. Smithy (mobile **2413**, Stables
room **2406**) for Kestrel as a narrow level-ceiling probe. His nominal source
level is 25, but DD4 can load him through level 27; the source HP range is
**316-945**. The ordinary HP-fuzz helper still rejects this wider range. The
new path requires a source-safe sentinel, sanctuary, a fitted lower-bound
damage window, and a maximum live level of character level plus two. Before
sanctuary or the opener, the endpoint will compare the exact GMCP HP ceiling
with Kestrel's audited **318-point** budget and withdraw if it is too high.

Runs **13019-13028** preserved safe recovery and research evidence: food and
sanctuary maintenance succeeded, the Forest wandering bear route did not find
its required claws, Circus and Mirror Realm fame routes were too strong, New
Ofcol was absent during bounded search, and the live questmaster refused a new
quest while fame was negative. Kestrel remains level 24 in healer room 3054;
the next live step is now a new source-approved route, because the Mr. Smithy
probe is closed by its measured HP. The current carrier implementation and
verification counts are recorded in the frontier section below.

### Current Evidence Correction: Ground And Carrier Gear Routes (September 11, 2026)

Run **13029** is recorded as a failed protected probe, not a pending
experiment: passive Mr. Smithy loaded at **474/474 HP**, above Kestrel's
**318-point** thief output budget, and the retreat produced a real net
**-384 XP**. The loss is preserved in SQLite and the transcript; no kill or
death occurred. Runs **13030-13032** restored sanctuary and food state, and
Kestrel's current durable checkpoint is **40225** at **332,185 XP**. Dorrik's
run **13033** returned safely after one source-known below-band rolling-rock
maintenance kill for **150 XP**, with no objective kill.

The source equipment report now sends direct ground-reset objects through the
same route-safety audit used by food and resource stashes, and the campaign
can pair a source-carrier placement with an exact one-kill hunt candidate.
A reachable clean route is marked `promising`; closed doors, movement
requirements, aggressive or scripted mobiles, specials, and crowds remain in
hazards or autonomy rejections. Future, unreachable, or unranked mob drops
remain `source-only` and are never campaign permission. Carrier execution also
requires a fitting live HP budget and post-kill loot/equip verification. An
unresolved source template is unknown and is rejected by the target, transit,
city, and encounter gates rather than treated as neutral HP. The full offline
suite passes **5,543 tests**; the affected equipment, hunt, campaign, starter,
progression, and CLI suite passes **3,637 tests**. No live carrier hunt is
launched while the saved checkpoints remain blocked by recovery or funding.

### Latest Liveness Hardening: Public HERO API (September 12, 2026)

The `hero` CLI and the Python `run_hero_request` entry point now share a
180-second live-segment default. A missing runtime cap is normalized to that
bounded value, and implicit reset waits remain disabled for bounded invocations;
larger runtime or reset budgets must be explicit. This makes library launchers
resumable and observable under the same contract as the CLI. The full offline
suite passes **5,590 tests**; this is a liveness improvement, not new live
progression or HERO proof.

### GMCP Alignment And Fame Inspection: September 14, 2026

The public `show-hunt-candidates` and `show-combat-readiness` commands now read
alignment from the nested GMCP `progress` snapshot used by `CharacterState`,
rather than looking only for a top-level field. They apply the same level-aware
rule as campaign admission: `50000` below level 10 is concealed, while a
level-10-or-higher value in DD4's `-1000..1000` range is authoritative. Kestrel's
real report now displays alignment **1000** and passes it into source candidate
ranking. The same reports now expose `character_fame` separately from
alignment, reading fame from nested GMCP `Char.Stats`; Kestrel's live value is
**-12**. This prevents the two independent DD4 reputation fields being treated
as one. Run **13255** confirmed the distinction during the Green Dragon probe:
the wire alignment remained **1000**, fame remained **-12**, and the target's
**576 HP** exceeded the **342-point** conservative output ceiling, so the bot
withdrew and lost **385 XP** without a kill. The exact policy is closed for this
boot; this evidence does not claim sustained progression or HERO proof.

### Protected HP Probe Admission: September 12, 2026

The source-ranked selector now surfaces a sanctuary-backed HP-fuzz probe when
the source lower bound fits the audited combat output, even if the loaded
upper bound does not. The readiness report exposes this as
`protected_hp_probe`; it does not relax the live GMCP HP gate. Run 13112
attempted the Tree Sprite frontier, but Magic Shop flight service refused
Kestrel's -12 fame. That remains useful funding evidence, not progression.
Runs 13113-13117 then completed bounded food and target checks; run 13117
reached Chaplain Jerrold at 416 HP and withdrew against the 318-point ceiling.
The campaign is now safely checkpointed at **40575** in healer room **3054**;
the latest resume opened no gameplay connection.

### Live Fallback Output Gate: September 12, 2026

The source-ranked selector now applies the fixed combat-output ceiling even
when protection recovery is using its tightly bounded no-reserve fallback.
This closes a live-state edge case where a known-disarm character could select
an armed target whose source HP ceiling exceeded the audited kill window.
Source-less policy fixtures retain their compatibility behavior; live states
must provide the source world and character class before this gate can be
applied. The campaign suite passes **1,464 tests** after the regression.

### Source-Backed Thief Upgrade Route: September 12, 2026

Source revision `622d5de` now registers a multi-step Thief equipment plan for
the next useful frontier. At level 26 or above, with a better piercing weapon
still needed, the campaign can source-audit buying lockpick object **38** from
Dave (mobile **3050**, room **3120**), practice `thief base` to 30% and `pick
lock` to 60%, then use the official Shadow Keep approach to unlock room
**16619** and target the exact smuggler mobile **16609** in room **16635**.
That mobile's equipped fine dagger is object **16614**. The source route costs
266 raw movement, or 74 while flying; `spec_thief` is admitted only with a
bounded exposed-coin loss and the existing sanctuary, HP, output, identity,
and healer-return gates. The complete route and practice chain are covered
offline, but live lockpick purchase, door entry, kill, and dagger acquisition
remain unproved. The full offline suite passes **5,645 tests**.

### Lockpick Funding Exception: September 13, 2026

At level 24 or above, a Thief who still needs the Shadow Keep lockpick can use
one source-audited maintenance route to fund it: Shargugh, mobile **6115**, in
room **6100**, carries iron ring object **6114** with a source value of 5,000
copper. The route is limited to 12 commands and 56 movement, retains the
`where drunk` preflight for its source `spec_drunk` hazard, and requires the
exact source mobile, room, object, HP, output, inventory, and safe-sale gates.
This below-band kill is a bounded funding objective, not progression XP; the
live reboot's sale price must still be verified before purchase.

### Moria Locator Recheck: September 13, 2026

Live run **13119** confirmed that DD4's `where` command reports visible target
names with room labels, but not room VNUMs. Moria's mobile **4055** wanders,
and several rooms share the label `The maze`; the runner therefore reached
source room **4063** after a positive locator result but found its room listing
empty. The locator now performs one bounded same-room `look` recheck when a
positive refresh has no movement path, then returns to normal exact-target and
`consider` gates. The run remains absence/recovery evidence with no kill, XP,
or HERO claim. The full offline suite passes **5,646 tests**.

### Moria Southern-Maze Locator Coverage: September 13, 2026

Run **13120** recorded Shargugh absent while funding Kestrel's future Shadow
Keep lockpick, and run **13121** positively located the Moria carrier but did
not acquire a purple potion. Source revision `622d5de` confirms that mobile
**4055** may wander through the reachable rooms **4063**, **4066**, and
**4065**, which all display as `The maze`; the western rooms **4057**, **4058**,
and **4062**, plus the aggressive branch at **4067**, remain excluded. The
deep locator now narrows to those three source rooms and preserves exact
visibility, identity, consider, hazard, and required-loot gates. Policy
revision **283** reopened only the prior same-boot, no-loss level-24 terminal
result, preserving its old attempt evidence. Live run **13124** then followed
the widened graph, killed source mobile **4055**, acquired the required purple
potion, and returned Kestrel safely to healer room **3054** for **100 XP**
without a death. Maintenance runs **13122** and **13123** acquired `some grain`
from Crystal rooms **10036** and **10038** without changing XP. Kestrel is
level 24 at **331,279 XP**. The full offline suite passes **5,648 tests**; HERO
proof remains outstanding.

### Lockpick Funding Shortfall Selection: September 13, 2026

The funding policy now remains executable when the progression layer selects a
lockpick shortfall but a generic source-frontier fallback would otherwise
replace it with an unavailable policy. Among candidates that already pass the
source, route, protection, movement, and saleability gates, a known currency
shortfall now prefers a carrier whose audited coins cover that shortfall over a
50-coin fallback. This is a ranking rule, not a safety override: the real
3,400-coin Solace carrier remains excluded because its route has multiple
attackers and no sanctuary reserve was available.

Live run **13125** exercised the repaired policy and killed the source Midget
for **40** below-band maintenance XP plus **50** copper, returning safely to
healer room **3054**. Runs **13126-13127** completed the next Circus and Mirror
Realm fame-recovery checks without XP change. Run **13128** then killed the
second permitted large-hobgoblin carrier, acquired the required purple potion,
and added **100** XP with a safe healer return. Kestrel is level 24 at
**331,419 XP**, checkpoint **40618**. Offline coverage passes **5,650 tests**
and compilation is clean; sustained progression and HERO proof remain open.

### Funding Handoff Repair And Live Guard Attempt: September 13, 2026

An excluded city-maintenance policy can no longer erase an active food, flight,
or Shadow Keep lockpick shortfall by falling through to a generic unavailable
frontier. The repair is limited to a fed, alive, non-combat checkpoint; the
source-safe funding selector still enforces identity, route, movement,
protection, output, saleability, and below-band rules. The full offline suite
passes **5,651 tests**, including the new checkpoint regression, and compilation
is clean.

Run **13132** completed the repaired handoff against patrolling guard mobile
**9400** in room **9400**, producing **90** below-band maintenance XP and **1
copper** of realized proceeds with no death or XP loss. Kestrel returned to
healer room **3054** at checkpoint **40633**, level 24 and **331,599 XP**. The
next policy correctly prioritizes a second purple sanctuary reserve before the
lockpick funding loop reopens. This is bounded maintenance evidence, not
sustained progression or HERO proof.

### Lockpick Shortfall Ahead Of Flight Retry: September 13, 2026

The campaign now gives an active Shadow Keep lockpick shortfall precedence over
a pending flight-purchase retry when the generic policy layer selects a flight
service handoff first. This keeps provision-funding executable while retaining
the existing healer, death, combat, route, protection, output, and source
candidate gates. The full offline suite passes **5,652 tests** and compilation
is clean.

Run **13133** completed the second permitted Moria carrier route, acquired the
second purple sanctuary reserve, and added **100** bounded maintenance XP with
a safe healer return. Runs **13134-13135** tested Circus and Mirror Realm fame
recovery; both ended as retryable source boundaries with no kill or XP change.
Kestrel is level 24 at **331,699 XP**, checkpoint **40642**, with **527 copper**
toward the **1,000-copper** lockpick. The current next policy is
`provision-funding`; sustained progression and HERO proof remain outstanding.

### Funding Precedence Live Check: September 13, 2026

Run **13136** exercised the pending-flight precedence and completed the
source-backed on-duty-guard funding route for **110** bounded maintenance XP
and **1 copper**, with no sale, death, or XP loss. Kestrel returned to healer
room **3054** at checkpoint **40645**, level 24 and **331,809 XP**. The ending
ledger has one verified purple sanctuary reserve and **528 copper**; the next
policy correctly returns to Moria sanctuary recovery before another funding or
progression attempt. This remains maintenance evidence, not sustained HERO
progression or HERO proof.

### Moria Reserve Recheck: September 13, 2026

Run **13137** re-entered the source-ranked Moria sanctuary-recovery route at
level 24. The required second purple was not present, so the segment ended
cleanly with no kill, XP change, death, or loss and returned Kestrel to healer
room **3054** at checkpoint **40649**. The ending ledger remains one verified
purple reserve and **528 copper**; the selector now rotates back to the active
lockpick `provision-funding` handoff. This is a bounded source boundary, not
sustained progression or HERO proof.

### Loose Sanctuary Reserve Precedence: September 13, 2026

Run **13142** confirmed that the Magic Shop still refuses Kestrel at fame
**-12**, leaving the flight retry as a bounded service boundary. Run **13143**
then recovered a large hobgoblin's purple potion for **90** maintenance XP and
returned safely to healer room **3054**. The potion initially remained loose
in inventory, so the campaign selector now gives `audit-combat-pouch`
precedence over money-container cleanup and lockpick funding. Run **13144**
placed the potion in the worn pouch with no XP change, death, or loss;
checkpoint **40674** is level 24 at **332,149 XP** with one verified reserve
and **532 copper-equivalent**. The full offline suite passes **5,653 tests**;
sustained progression and HERO proof remain outstanding.

### Funding Fallback And Provenance Repair: September 13, 2026

Runs **13145** and **13147** recorded bounded no-change funding scans. Runs
**13146** and **13148** completed source-ranked Midget maintenance kills for
**40 XP** each. Run 13146 exposed missing source identity on an exact
below-band stop; the runner now retains the mobile VNUM and policy while
keeping the kill non-objective. The follow-up dispatch repair also prevents an
empty funding scan from falling through to a flight purchase while the
1,000-copper Shadow Keep lockpick shortfall is active. Kestrel is at checkpoint
**40724**, level 24, **332,229 XP**, healer room **3054**, no verified purple
reserve, and **639 copper-equivalent**. The full suite passes **5,656 tests**;
sustained progression and HERO proof remain outstanding.

### Protection Wait Liveness Repair: September 13, 2026

The reset-aware runner now defers the exact current-level, current-reboot
protection boundary when no sanctuary reserve or executable independent route
is available. A capped invocation remains blocked; a run with explicit reset
retries returns `awaiting_area_reset` without opening a gameplay segment, then
performs only the bounded world-time probe after its single configured wait.
The live proof waited 180 seconds, completed world-time run **13150** without
discovering a newer reboot, and returned to `provision-funding` without a
second flight attempt. Kestrel remains level 24 at checkpoint **40724** with
**639 copper-equivalent** toward the **1,000-copper** lockpick. The full suite
passes **5,656 tests**; this is liveness and evidence progress, not HERO proof.

### Liquidation Execution And Funding Follow-up: September 13, 2026

The campaign now derives emergency-provision sale mode from actual inventory:
a stale funding marker no longer creates a resupply detour when food is already
carried. Focused regressions and the full offline suite pass **5,659 tests**;
compilation is clean.

Live run **13154** sold 16 carried items through four safe Midgaard shops for
**305 copper**. Run **13155** completed a source-backed maintenance funding
kill for **40 XP** and **52 copper**, and run **13156** sold the residual purse
for **2 copper**. Kestrel is safely at checkpoint **40755**, level 24 with
**332,269 XP**, healer room **3054**, and **998 copper-equivalent**. The final
2-copper lockpick shortfall has no eligible current-reboot funding target, so
the campaign is waiting for fresh area-reset or source evidence. Run **13157**
performed the exact source preflight after one bounded reset wait; the carrier
was still absent, with no kill, loss, or XP change. No sustained HERO
progression or HERO proof is claimed.

### Route-Scoped City Quarantine And Mage Continuation: September 13, 2026

Field-city departure evidence now retains the exact policy that encountered the
bounded obstruction. A same-level, same-reboot retry blocks that policy, while
another source-ranked route receives its own route preflight; legacy evidence
without a policy ID remains globally conservative. Live run **13162** validated
the repair with Astrevo: the Circus route completed the exact Bearded Lady kill
for **108 objective XP** and returned to healer room **3054** at checkpoint
**40787**, with no death or XP loss. The earlier cross-module suite passed
**5,667 tests** at that earlier checkpoint; Astrevo remains level 8 and HERO
remains unproved.

### Route-Only Loss Revalidation: September 13, 2026

The campaign now distinguishes a pre-combat transit loss from a failed target
fight. When one exact same-level, same-reboot source hunt ended before target
engagement, with full recovery and only a source-labelled below-band transit
hazard, the selector may arm one fresh route-only revalidation. The candidate
must still pass source identity, current-band, output, movement, route-program,
and ordinary live gates. The marker is consumed before connection, cleared by
a productive target result, and closed by another failure; it never authorizes
general retries or counts incidental maintenance kills as progression.

Live runs **13168-13170** validated the repair for Astrevo. The first exact
route produced a current-band kill, the next segment repeated it for **226 XP**,
and the selector then rotated to another Circus target for a further positive
result. Follow-up runs **13171-13177** recorded bounded city, crowd, and
watchdog boundaries, and run **13178** stopped before connection while awaiting
an area reset. Checkpoint **40837** records level **8**, **31,068 XP**, a safe
return to healer room **3054**, no new loss, and no pending route marker. The campaign
suite passes **1,489 tests**; the level-10 trainer transition, sustained level
gain, and HERO proof remain open.

### Source Refresh And Special-Contract Audit: September 13, 2026

The source mirror was pulled to `80cad011b8c17b5ffc8828edae9182271bf7e46e`.
The refresh adds an explicit `AFF_MINDLESS` trait and confirms that mobile
specials are resolved from three weighted slots, including body/archetype
defaults and area `#SPECIALS` `M`, `N`, and `P` overrides. The source parser now
tracks nested C initializer braces, so weighted vectors no longer hide the
archetype XP field, and inherited template procedures are included in hazard
analysis. The refreshed source parses 4,138 mobiles and 1,629 effective
special-bearing mobiles; the full offline suite passes **5,692 tests**.
This is parser and evidence freshness work only; no new live progression or
HERO proof is claimed.

### Capacity Metadata And Route Rotation: September 13, 2026

Campaign startup now rebuilds pending sack, backpack, and girdle metadata from
chronological successful or ready segment results. A later explicit vault claim
removes that item from legacy recovery, so a claimed container is not restored
on every resume. An overweight capacity claim can receive one healer-side
equipment relief pass before one retry; the pass preserves recovery and does
not authorize unrelated loot.

The source-ranked selector also honors retry-exhausted, throughput-limited, and
current-reboot crowd evidence when considering its last-policy fallback. Run
**13190** live-proved the large-sack claim after lodging an obstructing object;
run **13191** banked the remaining coins; and startup recovered interrupted run
**13192** before selecting Moria. The latest boundary is safe at healer room
**3054**, level **8**, **31,513 XP**, checkpoint **40956**. Focused persistence
and selector coverage is included in the full offline result: **5,701 tests
pass**.
