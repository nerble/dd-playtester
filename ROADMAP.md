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
3. **Rule-based starter bot.** Automate login, character creation/selection, the tutorial,
   basic movement, recovery, and safe failure handling.
4. **Reports.** Produce Markdown and JSON summaries with progress, failures, balance
   signals, and representative commentary.
5. **Campaign execution.** Add checkpoints, resume support, budgets, stuck detection,
   and controlled long-running progression.
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
