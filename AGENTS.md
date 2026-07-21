# Repository Guidelines

## Project Structure

The `dd4tester/` package contains the asyncio Telnet client, GMCP parser,
scenario runner, persistence layer, state model, and CLI. YAML scenarios live
in `scenarios/`; keep reusable scenarios small and non-destructive. Tests are
under `tests/`, with sanitized protocol samples in `tests/fixtures/`. Generated
SQLite databases and JSONL transcripts belong in `runs/` and `transcripts/`;
both directories are intentionally ignored by Git.

Never modify the Dragons Domain IV core repository from this project.
Treat its public source and area files as valid read-only evidence for routes,
resets, mob flags and levels, drops, shops, prerequisites, and mechanics.
Before training or automating a skill, read both its current in-game help and
its source implementation. Record whether it is active or passive, its legal
position and target, pulse/mana cost, effect formula, prerequisites, and any
equipment or status constraints; never infer behavior from the skill name.
Before source-backed research, and at least once per active working day,
fast-forward `runs/dd4-source` from upstream with `git pull --ff-only`; record
the revision used for consequential policy decisions.
Confirm dynamic behavior such as wandering, prices, and combat risk with live,
redacted transcripts before promoting it into an autonomous policy. Scope
prices, kill repetition, applicable object instance limits, and observed spawn
counts to the `DD was started at ...` reboot identity; never carry them across
reboots. Instance limiting applies only to the few objects whose source
definitions use it, not to mobiles.
Before HERO renaming is available, use source-backed keywords and keep active
gear directly accessible; put spare ambiguous items in containers or the vault.
Leave a depleted hunt area before waiting because occupied areas reset more
slowly.

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
For live progression, prefer one bounded multi-segment campaign process over
repeated one-shot connections. Before launching, verify no tester process is
already active.

## Operational Fail-Fast Policy

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

## Commits And Pull Requests

Use concise imperative commit subjects, for example `Persist character state
snapshots`. Include verification details and behavioral impact in pull
requests. Commit significant verified changes locally. About every third
milestone, push the complete intended scope to the configured GitHub remote,
merge it into `main`, and push the updated `main`; a failed push must not block
local testing. Never push generated run data, transcripts, secrets, or unrelated
user changes.
