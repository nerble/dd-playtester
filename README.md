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

Milestone 5 registers the proven creation/tutorial policy as its first segment.
Once it reaches level 2, the campaign checkpoints and blocks cleanly until a
verified leveling policy is added. It never fabricates a route or repeatedly
grinds unknown content; this safety boundary lets future policies extend the
same character toward HERO without losing campaign history.

## Progression Evidence

Inspect the currently registered policy for a class and level before launching a
campaign segment:

```powershell
python -m dd4tester show-policies --level 2 --class mage
```

The registry distinguishes `verified`, `research`, and `unavailable` policies.
The starter band is verified through level 2. Existing live DD4 captures register
the Mud School, Loremaster, and arena as a research-gated level-2-to-10 band for
every supported base class, including its class-specific practice candidate. The
campaign will checkpoint rather than attack until that combat and XP loop has
been demonstrated in sanitized evidence.

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

The command reports every prerequisite and required percentage from the source
snapshot. It is informational until live skill percentages are added to the
character state model.

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

Reports cover progression, failures, health and combat signals, and concise
first-person commentary derived from recorded evidence. They do not make AI
decisions or invent events. The optional `reports/` directory is local output
and is ignored by Git.
