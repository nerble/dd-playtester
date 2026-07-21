# Character-Independent Autonomy

DD4Tester targets any valid race, gender, base-class, and subclass combination.
Character names identify credentials and stored history only; they must never
select behavior.

## Data Flow

1. A character YAML profile supplies identity and local safety limits.
2. `data/archetypes.json` resolves class aliases, subclass relationships,
   capabilities, training defaults, stat priorities, and progression tracks.
3. Live GMCP, text observations, inventory, effects, reboot identity, and
   campaign history form a `ProgressionContext`.
4. The progression selector chooses an evidence-backed policy from that
   context. It may use capabilities or a configured track, but not a character
   name.
5. The deterministic executor applies shared navigation, provisioning,
   recovery, combat, death, inventory, and checkpoint safeguards.
6. Every command records its stage, reason, category, and safety-critical flag.
   Reports derive progress, decision analysis, feedback signals, and first-
   person commentary from those records.

## Policy Boundaries

- **Shared safety:** hunger, thirst, health, mana, movement, disarmament,
  encumbrance, death recovery, escape, saving, and quitting.
- **World knowledge:** routes, rooms, mobs, drops, shops, resets, and observed
  reboot-scoped facts.
- **Archetype policy:** usable abilities, practice prerequisites, combat
  resources, stat priorities, and equipment restrictions.
- **Level-band policy:** suitable targets, protection requirements, kill limits,
  recovery points, and fallback actions.
- **Execution adapter:** direct Telnet/GMCP is primary. A later Mudlet/VM adapter
  must consume the same decisions and emit the same observations.

## Representative Proof

`matrices/level-10.yaml` defines the first proof matrix: mage, thief, and
warrior characters with different races, genders, and subclass targets. The
matrix runner advances them round-robin, persists each campaign independently,
continues after an isolated failure, and succeeds only when all three reach
level 10. Live evidence, not configuration or unit tests alone, is required to
claim that proof complete.
