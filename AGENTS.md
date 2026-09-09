# Repository Guidelines

## Objective And Evidence

Build for every source-legal race, cosmetic
sex, base class, optional subclass, name, and personality, capable of creating
or resuming characters to HERO 100. HERO remains unproved. Follow
`docs/APPROACH_REVIEW_2026-09-08.md` and `ROADMAP.md`: fix roster-level
blockers, measure whole-session net XP, and avoid higher bands.
Names and credentials identify history, never behavior. Distinguish source
estimates, offline replays, live observations, and sustained progression.

## Structure

`dd4tester/` contains transport, observation/state, deterministic decisions,
campaign orchestration, storage, and CLI modules. Reuse behavior
modules; keep configuration in YAML. Tests and sanitized
protocol fixtures live in `tests/`. SQLite, transcripts, and HERO
workspaces belong in ignored `runs/`, `transcripts/`, and `runs/heroes/`.

## Development Commands

Use Python 3.12 from `.venv`. From the repository root:

```powershell
python -m pip install -e .[dev]
python -m pytest -q
python -m compileall -q dd4tester tests
python -m dd4tester run scenarios/login.yaml
```

These install dependencies, run offline tests, check compilation, and execute
a scenario. Follow `README.md` for bounded live runs and inspection commands.

## Style And Tests

Use four-space indentation, type hints, `snake_case`, and `PascalCase` classes.
Prefer structured parsers and helpers. Keep changes scoped; preserve
unrelated worktree changes. Name pytest cases `test_<behavior>` in
`test_<module>.py`. Reproduce live failures with sanitized, timed event replays,
including negative and survival cases. Run focused tests, then the full suite.

## Runtime Contracts

Read `docs/OPERATIONS.md` before live work or user commentary. Source-audited
capability registration plus positive practice and action-specific gates are
required for dispatch; observed skill names alone authorize nothing. Preserve
loss evidence, exact live targeting, bounded retries, and healer recovery.
Use `docs/history/AGENTS_2026-09-08.md` for gameplay contracts; search
the affected topic before changing its behavior. Preserve distinct labels,
nested closed exits, and synchronized observed and verified resource ledgers. A visibility-dependent route requires positive practiced
authorization plus a fresh affect; it cannot bypass detecting, scripted, or
unknown mobiles. Combat-only specials follow source aggression cutoffs during
transit; pre-combat, scripted, equipped, unknown, and engaged hazards remain
blocked. AI personality
generation does not authorize AI gameplay.

## Security And Changes

Use Windows Credential Manager; never place secrets in YAML, logs, or tests.
Preserve non-secret persona metadata in run context. Keep changes local: no
pushes, remote merges, or PRs. At most one local commit per 24 hours, at 9:00 PM
Pacific/Auckland, with a 60-second timeout and no retry for 24 hours. Use concise
imperative commit subjects. Update usage and proof status when behavior changes;
keep historical run narration out of these operating instructions.
