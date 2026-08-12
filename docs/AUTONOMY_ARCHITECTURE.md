# Character-Independent Autonomy

DD4Tester targets any valid race, gender, base-class, and subclass combination.
Character names identify credentials and stored history only; they must never
select behavior.

## Current Boundary

The deterministic Telnet/GMCP path is the product boundary under active
development. Mudlet consumes the same command and observation contract, but
Mudlet profile automation and Windows VM lifecycle control are validation work,
not alternate decision engines. AI decisions are intentionally absent until
the deterministic path can be replayed and measured.

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

## Policy Lifecycle

The selector must distinguish three states. `verified` is reusable executable
evidence. `research` is a bounded live probe with explicit route, combat,
resource, and return limits. `unavailable` is a durable safe stop explaining
what evidence or implementation is missing. A checkpoint, source catalog
entry, policy count, or research result is not a progression proof by itself.

Source identity is part of the policy key: area, mobile VNUM, reset room,
character level, and reboot identity are retained separately. Same-reboot
productive XP may carry a safe repeat across a level boundary when the source
identity is unambiguous and the normal live presence, consider, crowd, health,
equipment, and recovery gates still pass. Research candidates must not hide
such a repeat. Promotion requires objective XP, bounded damage and resource
evidence, loot or funding evidence where relevant, and a safe healer return.

## Current Proof And Debt

The live mage/thief/warrior matrix proves level 10. Representative long-running
campaigns currently anchor Aeloria at level 13, Dorrik at level 12, and Kestrel
at level 24. The missing proof is a fresh uninterrupted creation-to-HERO run,
generic class/subclass executable coverage after level 30, and the Mudlet/VM
visible-client boundary. The next implementation work therefore expands the
class-aware level-band registry and its promotion tests before adding model
based decisions.

## Policy Boundaries

- **Shared safety:** hunger, thirst, health, mana, movement, disarmament,
  encumbrance, death recovery, escape, saving, and quitting.
- **World knowledge:** routes, rooms, mobs, drops, shops, resets, and observed
  reboot-scoped facts.
- **Archetype policy:** usable abilities, practice prerequisites, combat
  resources, stat priorities, and equipment restrictions.
- **Level-band policy:** suitable targets, protection requirements, kill limits,
  recovery points, and fallback actions.
- **Execution adapter:** direct Telnet/GMCP is primary. The Mudlet shared-file
  bridge consumes the same decisions and emits the same GMCP/text observations;
  VM and profile lifecycle automation remains a separate validation boundary.

## Representative Proof

`matrices/level-10.yaml` defines the first proof matrix: mage, thief, and
warrior characters with different races, genders, and subclass targets. The
matrix runner advances them round-robin, persists each campaign independently,
continues after an isolated failure, and succeeds only when all three reach
level 10. Live evidence, not configuration or unit tests alone, is required to
claim that proof complete.

Use `python -m dd4tester matrix-coverage <matrix.yaml>` to inspect both
declared source-legal pair coverage and persisted target-level evidence. The
two counts are intentionally separate: a generated entry is not validation
until its campaign checkpoint records the matrix target level.
