# Progress Audit: 2026-08-12

## Master Goal (Refined)

The product goal is one character-independent engine that accepts a
source-legal race, cosmetic sex, base class, optional subclass, name, and
personality, then creates or resumes that character and plays autonomously to
HERO level 100. A name identifies credentials and history only; it must never
select a route or behavior. Direct Telnet and GMCP remain the primary
development adapter. Mudlet in a Windows virtual machine is a later visibility
and integration boundary, not a substitute for deterministic game logic.

The goal is proved in layers. Creation and the tutorial must work first;
representative base classes must then cover level 10; every class needs
executable, source-backed bands through subclass transition at level 30; the
engine must cover the middle and high bands; and finally a fresh, uninterrupted
creation-to-HERO run must complete without steering. Sex is preserved in
identity but is not a separate progression coverage dimension.

## What Is Proven

- Async Telnet, Telnet negotiation, GMCP capture, redacted transcripts, YAML
  scenarios, SQLite persistence, resumable campaigns, and pytest coverage are
  operational.
- The rule-based starter creates or resumes characters, completes the tutorial,
  provisions, trains, reaches level 2, saves, and quits.
- The live mage/thief/warrior matrix reaches level 10 with contrasting race,
  sex, and subclass requests.
- Campaign checkpoints, bounded segments, source-backed route selection,
  training, equipment stances, provisions, money loops, combat recovery, and
  death/corpse recovery have substantial live evidence.
- Current representative campaign anchors are Aeloria mage level 13, Dorrik
  warrior level 12, and Kestrel thief level 24. Kestrel's level-24 Dwarven
  Home host route most recently yielded 1,006 XP and returned to healer room
  3054 at full HP and mana.
- Offline regression coverage is now 2,485 passing tests. Live continuation
  recorded Dorrik's level-12 route hazard at Dwarven Home (run 5054), then
  rotated without manual steering to the Shire receptionist for 584 XP (run
  5055) and a two-kill Fleshmonger circuit for 519 XP (run 5056). He is at
  61,542 XP, 8,508 short of level 13, safely recovered in healer room 3054.
- Source-ranked route scoring now recognizes `spec_fido` and other source-
  proven noncombat specials as safe transit occupants. It retains their
  hazard evidence but no longer rejects an otherwise safe target because of a
  large below-band noncombat crowd; ordinary aggressive crowds remain gated.

## What Is Not Proven

- No fresh character has completed an uninterrupted level-0-to-100 run.
- Generic executable coverage is incomplete for the full base-class and legal
  subclass matrix, especially after level 30 and above the current frontier.
- A checkpointed level-100 campaign is not evidence that every missing band is
  solved. `verified` policies are executable proof; `research` policies are
  bounded probes; `unavailable` policies are explicit stops.
- Mudlet profile automation, VirtualBox lifecycle control, and visible client
  commentary have not yet passed an end-to-end acceptance run.
- AI decision-making is intentionally out of scope until deterministic policy
  coverage and replay are reliable.

## Architectural Assessment

The architecture has the right major boundary: protocol and observations feed
state and storage; source catalogs and class data inform policy; the campaign
selector chooses a level-band action; the deterministic executor performs it;
reports and commentary derive from stored events. Reboot identity, mobile and
object VNUM namespaces, live GMCP exits, and bounded failure recovery are now
first-class evidence rather than text heuristics.

The main debt is policy lifecycle. Large shared modules contain valuable
knowledge, while declarative class analysis and generated source candidates are
not yet a single auditable registry. A fresh research candidate must never hide
a productive repeat, and legacy objective kills need durable source identity so
their XP can be reused at the next character level. The current selector fix
and regression test close that specific rotation failure. The next structural
improvement is to make policy status, evidence, and promotion explicit per
class, subclass, level band, source mobile, and reboot.

## Refined Work Order

1. Keep the selector frontier productive: carry source-identified rewards across
   level boundaries, rotate safe repeats, and test every fallback path.
2. Build an executable class-aware matrix for levels 1-30, including practice
   gateways, equipment roles, and confirmed subclass transition at 30.
3. Expand source-backed routes one level band at a time through 31-70, then
   71-100, promoting only after live XP, safety, resource, and return evidence.
4. Add replay, soak, disconnect, death, reboot, and stale-process tests around
   a fresh creation-to-HERO campaign.
5. Validate the same decisions through Mudlet and VirtualBox, then improve
   humanlike progress commentary. AI remains an optional later layer.

## Definition Of Done

The master goal is complete only when one command can create or resume any
source-legal request, run to level 100 without manual gameplay, survive normal
restarts and recovery cases, persist an auditable report, and pass fresh proof
for every base class plus legal race/class pairings at level 10. High-level
policy coverage, visible-client automation, and commentary must be demonstrated
by runs, not merely declared in configuration.
