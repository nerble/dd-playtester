# Autonomous Playtesting Roadmap

The target is an autonomous character that can progress from character creation
to HERO level 100, explain its experience in humanlike language, and run either
headlessly or through a visible Mudlet client in a Windows virtual machine.

## Delivery Principles

- Use direct Telnet and GMCP runs to develop and repeat game behavior quickly.
- Keep observations, state, decisions, commands, and commentary as separate layers.
- Preserve every raw input beside derived data so a failed decision can be replayed.
- Make campaign runs resumable; a level-100 test must survive process and VM restarts.
- Keep AI optional until deterministic behavior and safety boundaries are measurable.

## Practical Milestones

1. **Structured observations — complete.** Convert text and GMCP into typed events
   such as room entry, prompts, health changes, combat, quests, items, levels, and death.
2. **Character state — complete.** Build current state from events and persist
   timestamped snapshots.
3. **Rule-based starter bot - complete.** Automate login, character
   creation/selection, the tutorial, basic movement, recovery, and safe failure
   handling.
4. **Reports - complete.** Produce Markdown and JSON summaries with progress, failures,
   balance signals, and representative run-time commentary.
5. **Campaign execution foundation - complete.** Add checkpoints, resume support,
   budgets, stuck detection, and controlled long-running progression.
6. **Mudlet bridge.** Create a small Lua integration that exchanges commands, output,
   GMCP, and commentary while leaving the normal client visible.
7. **VirtualBox orchestration.** Start and monitor a Windows VM, launch the Mudlet
   profile, collect artifacts, and recover from client or VM failure.
8. **Humanlike commentary.** Turn important events and decisions into concise progress
   notes, observations, frustrations, and game-experience feedback.
9. **AI-assisted policy.** Introduce constrained model decisions for unfamiliar
   situations only after deterministic replay, limits, and evaluation are in place.

## Milestone 1 Exit Criteria

- Text and GMCP parsers are deterministic and independently tested.
- Structured events are written to both JSONL transcripts and SQLite.
- Raw responses and GMCP messages remain unchanged and auditable.
- New DD4-specific examples can be added as fixtures without changing the runner.

Milestone 1 was validated against a bounded live DD4 capture. Sanitized fixtures
cover the server's actual room/prompt format and `Char.Base`, `Char.Vitals`,
`Char.Stats`, `Char.Worth`, `Char.Affect`, `Char.Items`, and `Room.Info` GMCP.

## Milestone 2 Exit Criteria

- The same ordered game events always reconstruct the same character state.
- State covers identity, level and XP, resources, room, exits, stats, currency,
  inventory, affects, quests, combat, and death.
- Every meaningful state change creates a revisioned transcript event and a
  timestamped SQLite snapshot linked to its source event.
- Repeated GMCP does not create duplicate state revisions.
- `show-state` exposes the latest state and complete revision history.

Milestone 2 was validated with deterministic fixture replay and a bounded live
DD4 capture, including text-room enrichment from the later `Room.Info` GMCP.

## Milestone 3 Exit Criteria

- A YAML profile selects name, race, gender, base class, and optional level-30
  subclass target without storing a password.
- Character creation and reconnection are deterministic and transcripted.
- The bot completes the prelude, obstacle course, all required training fights,
  final gladiator/key sequence, and Victory portal.
- It recovers below 25% health, provisions food and water, equips tutorial
  rewards, practices an available class ability, reaches level 2, saves, and
  quits.
- Runtime, command, reconnect, and repeated-command limits stop stuck runs.

Milestone 3 was validated live with a newly created Human female Mage targeting
Warlock. The bot reached level 2 during advanced training, completed the final
combat and provisioning steps, practiced `magic missile`, saved, and quit.

## Milestone 4 Exit Criteria

- `report` renders the same stored run as either concise Markdown or structured JSON.
- Reports show level, XP, health, room, combat, item, and quest progress when observed.
- Failed runs and detected character deaths are called out directly.
- Balance signals report observed progression, combat, and low-health pressure without
  claiming conclusions beyond the recorded evidence.
- First-person commentary is deterministic, traceable to stored decisions and game
  events, and never includes redacted commands or secrets.

## Milestone 5 Exit Criteria

- A campaign YAML binds a character profile to a target level and aggregate limits.
- Campaign, segment, and checkpoint rows survive process restarts in SQLite.
- The campaign resumes its last checkpoint by default and can explicitly start fresh.
- Segment, command, runtime, and stalled-progress limits stop unsafe repetition.
- The verified starter policy is executed as the first campaign segment; unimplemented
  post-tutorial territory blocks with an explicit checkpoint instead of guessing.

This completes the campaign execution foundation, not a claim that every class
already has a verified level-2-to-HERO policy. The next progression work must
collect live evidence for safe XP routes, class abilities, recovery, equipment,
and failure handling before registering each new level-band policy.

## Progression Evidence Cycle 1

- Registered the level-2-to-10 Mud School band as research-gated for every base
  class, with class-specific practice candidates.
- Preserved the live evidence: the entrance links to the Loremaster and arena;
  the Loremaster advertises training through level 10; and observed arena rooms
  contain low-tier opponents with safe exits.
- Kept the policy non-executable until a bounded live run proves the combat, XP,
  recovery, and exit sequence. Campaigns now identify this precise gate instead
  of reporting only a generic missing policy.
