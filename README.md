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
revisioned character snapshots. AI decision-making is intentionally not
implemented yet.

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
