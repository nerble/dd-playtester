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
Treat VNUMs as separate namespaces: room, mobile, object, and object-set VNUMs
are unique within their category, but the same number may appear across them.
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
Before training or automating a skill, read both its current in-game help and
its source implementation. Record whether it is active or passive, its legal
position and target, pulse/mana cost, effect formula, prerequisites, and any
equipment or status constraints; never infer behavior from the skill name.
Apply character titles and descriptions only during initial identity setup;
use persisted command evidence to avoid recreating them on later logins.
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
Before a live area launch, parse each registered mobile's exact area-file room
description through the target recognizer; use live output to confirm presence
and dynamic reset state, not to discover static mobile display lines.
Never attack for XP when `consider` returns a `do_consider` result from the
`diff <= -5` or `diff <= -10` branches; those targets are too low to be useful.
Treat `hide` as a stationary ambush or avoidance skill because ordinary
movement removes it; do not use it as travel concealment.
Before a mage field fastwalk, establish known invisibility at recall so
wandering Midgaard greet-program mobiles cannot replace a productive target
with a trivial forced fight.
For verified hunts, continue until a meaningful discomfort threshold: low
health without vetted local recovery, an uncured disabling affect, unusable
food or water when needed, insufficient movement, encumbrance, or exhausted
local targets. Prefer source-vetted local sleep and multi-target circuits over
recalling after one safe kill. Before an imminent level, issue `train` for the
class profile's current primary stat and wear all legal stat-improving gear.
Tune autonomous field play 10% more aggressively than the current baseline:
tolerate recoverable damage, use 264-second bounded fights, continue circuits
at 40.5% health with 13.5% mana and 9% movement, leave the healer at 67.5%
health and 27% mana, ordinarily withdraw at 27% health, and finish a
lower-level half-dead opponent down to 18%. Keep death traps, unknown
high-level enemies, unsafe crowds, disabling affects, and unsupplied hunger or
thirst as hard withdrawal boundaries.
Do not count source-proven or live-level-confirmed below-band mobiles as an
unsafe crowd. They must not block selection of a useful-band target or trigger
a flee when they join its combat. Never select them deliberately for XP, but
finish unavoidable trivial combat so it cannot stall the productive hunt.
Before HERO renaming is available, use source-backed keywords and keep active
gear directly accessible; put spare ambiguous items in containers or the vault.
Never guess object or mobile command keywords when the entity exists in the
public source. Parse and use its source keyword list; display-text noun
inference is only a temporary fallback for genuinely uncatalogued live
entities and must not be promoted into policy without source confirmation.
Treat profession-visible empty `eq all` slots as equipment debt. Prefer usable
mob drops, then inexpensive class-legal Midgaard basics; after major gear loss,
revisit Mud School first and repeat its course to recover free starter drops.
Never wear a finger item that applies a strength penalty. For low-level
characters with two legal finger slots, prefer two pink ice rings from the two
ring-bearing old dolls reset in Dwarven Daycare room 6605; each gives +1
strength and +6 hit points. An empty oversized container may be lodged
temporarily to make room for required drops only after `look in` proves it is
empty.
A registered one-off gear recovery may attack a source-proven low-level carrier
after a below-band `consider`, but must record that the kill is solely for a
required missing item and never treat it as an XP policy.
For mages, treat `summon familiar` as a source-backed risk-control candidate:
cast it outdoors, group the follower, and order it to open combat only after a
live bounded probe. Account for the spell's 100-mana cost and the familiar's
level-weighted group XP dilution; do not use it for trivial required-loot kills.
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
source-defined teacher bases reject lower-level characters. For thieves, raise
Stealth Techniques to its 60% prerequisite, then prioritize backstab while a
piercing weapon is equipped.
Persist trainer-cap and trainer-level practice rejections for the current
character level so later segments choose another eligible priority. Clear that
exclusion after levelling; do not persist prerequisite rejections because
another skill learned at the same level may unlock them.
Treat an `eq all` line containing `[weapon] -` as an empty slot, never as proof
of a wielded weapon. A dedicated rearm run must buy, wield, and verify an
occupied weapon line before succeeding. If the source-backed dagger is
unaffordable, use the existing Dragonhoard Bank credit route, then retry and
return to healer room 3054.

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
Treat the file as append-only development history; do not rewrite or remove
earlier entries. Write an entry before or as the corresponding response is
sent so a stalled task cannot leave the visible discussion unrecorded.

## Commits And Pull Requests

Use concise imperative commit subjects, for example `Persist character state
snapshots`. Include verification details and behavioral impact in pull
requests. Follow the local commit schedule above and leave remote publishing to
the user. Never stage generated run data, transcripts, secrets, or unrelated
user changes.
