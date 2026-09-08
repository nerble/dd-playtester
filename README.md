# dd-playtester

An experimental autonomous Dragons Domain IV playtester using asyncio Telnet,
GMCP, source-backed deterministic policies, and durable run evidence.

**HERO 100 is not yet demonstrated.** Creation, tutorial play, reporting, and
resumable campaigns work. The highest roster level is 25; the fresh-creation
track is 8. See the [current review](docs/APPROACH_REVIEW_2026-09-08.md) for
measured results and the [roadmap](ROADMAP.md) for remaining acceptance gates.

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

A roaming city obstruction can trigger up to three 12-second healer waits
within a shop segment, each followed by a fresh location check. Persistent
obstruction normally stops travel. Invisibility requires source authorization,
positive observed practice, sufficient mana, and an awake noncombat state;
class and level alone do not authorize a cast.

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

Latest full offline verification: **4,670 tests pass**. Tests do not establish
live progression. The [contributor guide](AGENTS.md) defines coding, evidence,
and local-only commit rules. The [preserved README](docs/history/README_2026-09-08.md)
retains earlier details and run history; superseded defaults there are not the
current operating contract.
