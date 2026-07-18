# dd-playtester
Automated play-testing and balance-analysis system for Dragons Domain IV.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
$env:DD4_USERNAME = "your-test-character"
$env:DD4_PASSWORD = "your-test-password"
python -m dd4tester run scenarios/login.yaml
```

The project connects over asyncio Telnet, records transcripts, captures GMCP,
loads YAML scenarios, and stores run evidence in SQLite. Its observation layer
derives deterministic `game_event` records for rooms, prompts, health, combat,
quests, items, levels, and deaths. A state reducer turns those events into
revisioned character snapshots. The starter bot uses explicit rules only; AI
decision-making is intentionally not implemented yet.

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

## Run data

With the default `scenarios/login.yaml` values, running from this repository root writes:

- SQLite database: `runs/dd4tester.sqlite3`
- JSONL transcripts: `transcripts/<scenario-name>-<run-id>.jsonl`, for example `transcripts/login-1.jsonl`

The SQLite schema has three tables:

- `runs`: one row per scenario run, including status, start/end times, scenario path, transcript path, and error text.
- `events`: one row per command, response, GMCP message, runner state, or derived
  `game_event`. Structured event payloads contain `type`, `source`, and `data`.
- `state_snapshots`: timestamped character-state revisions linked to the
  `game_event` that caused each change.

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
