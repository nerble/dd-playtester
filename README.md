# dd-playtester

An experimental autonomous Dragons Domain IV playtester using asyncio Telnet,
GMCP, source-backed deterministic policies, and durable run evidence.

**HERO 100 is not yet demonstrated.** Creation, tutorial play, reporting, and
resumable campaigns work. The highest roster level is 25; the fresh-creation
track is 8. See the [current review](docs/APPROACH_REVIEW_2026-09-08.md) for
measured results and the [roadmap](ROADMAP.md) for remaining acceptance gates.

The current live frontier is Kestrel, level 24 at 332,692 XP. Runs 12948-12984
added durable evidence: source damage and crowd gates rejected unsafe targets,
food was replenished, a below-band Midget completed a flight-funding action,
loot was sold, and the widened Moria carrier locator recovered a purple
sanctuary potion. Runs 12972-12978 completed safe food, recovery, and frontier
probes; run 12979 verified that the purple pouch ledger survives a fresh live
resume. Run 12980 reached the Ultima target and run 12982 reached Mahntor;
source HP and damage gates rejected both without combat or new loss. Run 12981
replenished food at Haon. Run 12984 reopened the source-validated Forest upgrade
after fresh damage evidence, then withdrew safely when room 18027 contained the
registered swarm crowd. The latest durable checkpoint is 40031 in healer
room 3054 with 2 gold, 18 silver,
and 79 copper (2,979 copper-equivalent), a 131-copper flight quote, one
funding cooldown step, and one purple potion in the combat pouch. Funding and
required-loot kills remain separate from objective-eligible progression. HERO
and sustained progression remain unproved.

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

`--segments` limits checkpoint segments. An explicit `--max-segment-runtime 180`
enables a short continuation and defaults reset retries to zero. Add
`--reset-retries 1 --reset-wait 180` for one wait outside a depleted area.
Without an explicit runtime override, reset retries default to the segment
budget. Live cleanup has its own allowance.

Use at least two segments when a reset wait may need a world-time probe before
field selection. The probe consumes a segment. A fresh response confirming the
same reboot after the completed wait permits reselection; an area reset does
not require a reboot. Missing observations and ordinary loss, route, resource,
and protection gates still block execution. `--retry-stalled` permits one bounded
frontier rotation, not a safety override.

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
The displaced-target behavior is replay-tested, not yet live-validated.
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
and preserves corpse looting. This is not character progression; ordinary
player XP must still be observed. The opening-death fix is replay-verified.

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
transcripts; route safety accepts only a level-aware 300..1000 value because
`spec_guard` assists characters below 300 alignment. Raw packets remain
unchanged in transcripts.
A confirmed healer-origin departure deferral stops the current invocation after
its existing short waits. It consumes the segment but not a funding-target or
hunting-endpoint attempt. Resume later for a fresh city check; this outcome does
not automatically spend an area-reset retry or rotate through other blocked
destinations. The checkpoint reason is `field_city_departure_blocked`.

A below-band target is still skipped for XP. If it has already attacked at its
registered endpoint, one exactly identified ordinary enemy may use the existing
30-second combat-finishing budget instead of an automatic XP-losing retreat.
Source hazards, fresh health/mana, nutrition, extra attackers, and command
acknowledgements still govern continuation. Its kill is incidental, never a
repeatable XP objective. Inspect `campaign_fastwalk_encounter_budgets` for the
`below-band-endpoint-defense` audit; no new CLI option is required.

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
promising row does not authorize combat or claim live availability, and source
class-slot coverage remains an active expansion area.

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

Latest full offline verification: **5,477 tests pass**. Reconnect accounting
preserves verified XP decreases first observed after disconnection, without
double-counting or inventing their cause. Campaign startup now preserves
campaign-owned potion and source-resource ledgers when a raw live snapshot
omits those fields. Fresh source combat-budget evidence can reopen a previously
cleared Forest upgrade without erasing its crowd quarantine. Run 12984 recorded
that retry and withdrew at room 18027; Kestrel checkpoint 40031 remains level 24
at 332,692 XP, alive in healer room 3054. The latest focused Moria and locator
regressions also pass; the nine-endpoint fallback remains within the shared
24-step movement bound.

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
mosquito and wasp instances formed a crowd. Kestrel is level 24 at 332,692 XP
at checkpoint 40031, with no new loss; the recovery marker still requires a
protected productive hunt. HERO remains unproved.

Use the source checkout refresh command above before source-sensitive planning;
do not treat a live observation or static source estimate as proof of a kill.
The full offline suite passes **5,477 tests**, and the current source mirror is
up to date.
