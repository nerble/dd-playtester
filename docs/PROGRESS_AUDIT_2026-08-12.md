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
- Current representative campaign anchors are Aeloria mage level 13 at 74,825
  XP, Dorrik warrior level 12 at 65,469 XP, and Kestrel thief level 24 at
  360,704 XP. Dorrik's bounded continuation completed runs 5103 and 5106 for
  531 XP and returned safely to healer room 3054.
- Offline regression coverage is now 2,490 passing tests. Dorrik's current
  frontier remains safe and productive: the Shire receptionist and
  Fleshmonger routes returned him to healer room 3054 without manual target
  steering. Aeloria remains at 74,825 XP, with sanctuary recovery explicitly
  waiting through its current-reboot cooldown; Kestrel's negative-fame campaign
  now reports its cure-critical reserve cooldown before unrelated crowd waits.
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
and regression tests close both the repeat-rotation failure and the reconnect
clear-marker oscillation. Reconnect repair now restores clear decisions only
from explicit retry events, while an active sanctuary cooldown is surfaced as a
protection wait before unrelated crowd handling. The next structural
improvement is to make policy status, evidence, and promotion explicit per
class, subclass, level band, source mobile, and reboot.

The latest route audit also corrected a concrete source mismatch. In
`daycare.are`, mobile VNUM 6605 is loaded in room 6605 twice, but the single
`E 1 6601` reset equips only the last loaded doll with the pink ice ring;
room 6603 is a wanderer observation point, not a ring-bearing reset. The
required-loot exception now targets the source room and one carrier attempt,
then lets the existing reboot-area cooldown obtain the second ring later. This
keeps low-value required-loot kills bounded and source-auditable.

The follow-up execution fix makes this source boundary executable. A static
required-loot stop may pass through a room where its mobile has wandered, but
`source_reset_room_vnum` prevents both field interception and ordinary target
evaluation until the registered reset room is reached. The new regression
proves the Day Care nanny is ignored in room 6603 and considered in room 6602;
this is generic route behavior rather than a character-specific exception.

The next route audit found a second generic boundary in run 5102. A
source-ranked wandering target was intercepted during the official outbound
fastwalk and rejected by live `consider` in room 4011. The runner then treated
the later relative circuit segment as if it still began at room 4011, even
though the official route had safely reached room 4022, and requested a
non-adjacent room 4010. The starter now snapshots and restores the outbound
hunt context for rejected interceptions, completes the official endpoint, and
only then resumes relative source stops. A focused regression and the full
2,490-test suite cover this invariant.

The conversation streamer was checked against the source log as part of the
same audit. Its configured speaker set includes `USER`, and live delivery
confirmed both missing steering records with an empty queue and an offset at
the source-file end. The current DD4 source revision used for this decision is
`044aa2e`.

## Refined Work Order

1. Keep the selector frontier productive: carry source-identified rewards across
   level boundaries, rotate safe repeats, and test every fallback path. Preserve
   event-specific cooldown decisions across reconnects.
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
