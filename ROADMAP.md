# Autonomous Playtesting Roadmap

## Master Objective

Given only a source-legal race, cosmetic sex, base class, optional subclass,
name/personality, and credentials when resuming, create or resume a character
and autonomously reach the requested level, up to HERO 100. Preserve progress,
explain the experience, and support direct Telnet and visible Mudlet operation.

**Not complete:** no HERO character is proved. Highest actual frontier is 25;
the fresh-creation track is 8. The active goal remains this master objective.
The [September 8 review](docs/APPROACH_REVIEW_2026-09-08.md) is the current work
order; dated run evidence belongs there, not in an expanding policy changelog.

## Delivered Foundations

- Async Telnet negotiation, GMCP capture, transcripts, SQLite, and inspection CLI.
- Deterministic observations, character state, checkpoints, and replay tests.
- Parameterized creation, the starter tutorial, and early character development.
- Run/campaign reports with evidence-grounded commentary and persona metadata.
- Public `hero` entry point, resumable campaigns, credentials, bounds, and recovery.
- Shared source-backed combat, training, equipment, travel, and resource policies.
- Mudlet bridge interface; this is not full VM lifecycle or HERO validation.

These have implementation and varying amounts of live proof. Their existence
does not mean every race/class or level band works end to end.

## Immediate Delivery Gate

1. Validate the timed combat probe through public runs without reopening lost
   routes or issuing manual attacks. The reset-probe handoff now has live proof
   in runs 12769-12770; it automatically proceeded to an 86-XP orc kill.
2. Advance the fresh character to 9 and through the level-10 trainer transition.
3. Demonstrate three consecutive bounded public invocations with positive
   combined net XP, repeated useful kills, autonomous maintenance, and a level
   gained. Include travel, recovery, provisions, and failed hunts in the cost.
4. Use existing thief, mage, and warrior campaigns for shared-behavior
   comparisons at their actual frontiers. Fix the largest measured bottleneck.

Flight shopping now uses the shared source-bounded city-greeter contract and
completed a live purchase/quaff/healer return in run 12781. No interruption
occurred, so its one-fight defensive path has offline proof only. Next measure
useful kills and travel amortization with flight active, and address the actual
target-pool or combat bottleneck exposed by that continuation.

Latest offline corrections: current-field crowd priority, same-reboot reset
handoff, elapsed-time damage sampling, and a deterministic deadline regression.
Travel invisibility now requires practiced authorization; shop obstruction uses
bounded rechecks. Fresh local targets supersede unengaged wandering pursuit.
Reconnect repair now attributes circuit kills to the observed stop rather than
the headline, and the legacy migration no longer rewrites modern terminal data.
Run 12785 exercised the restored selection but found absence/crowding; a later
rotation earned 109 XP from the hermit crab. Next assess the actual three-target
Moria crowd and avoid unproductive early repeats of a just-completed single-target
route. Preserve source assistance, health, and recorded loss constraints.
Repeated same-name instances now share bounded bystander considers. Only
positive below-band evidence discounts them; an XP target needs its own fresh
consider. Source combat retains that chosen instance across room/GMCP updates.
Current Telnet GMCP can repeat the primary opponent instead of identifying
each attacker; duplicate records are not independent identity evidence.
Run 12790 live-validated three exact-instance probes: two possible useful
combatants and one below-band bystander, with no XP. The next capability is a
bounded two-instance encounter, not another identical inspection. The new
source-estimated pair controller now passes timed offline replays for both
kills, exact selectors, practiced-spell cost, and survival/expiry failures.
It shares ordinary action dispatch and retains existing loss history.
Full verification passes 4,670 tests. Fresh live proof and sustained levelling
remain separate requirements; current evidence is in the active review.

## Subsequent Gates

| Gate | Acceptance |
| --- | --- |
| Sustained progression | Repeated productive journeys, training/equipment changes, and interruption recovery without steering |
| First HERO | One fresh creation-to-100 campaign with inspectable runs, losses, checkpoints, and report |
| Class coverage | One fresh HERO per base class across multiple races; source-audited legal subclass behavior |
| Race coverage | Each legal race/base-class pair reaches 10; sex is cosmetic, not another coverage axis |
| Visible operation | Same behavior through Mudlet in a Windows VM, with commentary, artifacts, restart, and failure recovery |
| Personality and analysis | Humanlike feedback grounded in actual events and configured persona |

Extend only the next needed band after lower-band executable proof. AI decision-
making remains deferred until deterministic behavior is replayable; generated
personality does not imply executable action authority.

## Measurement And Architecture

Report net XP, useful objective kills, losses/deaths, and connected time; report
reset, setup, and development time separately. Never present maintenance XP or
static coverage as autonomous progression. A safe checkpoint is recovery proof,
not a successful levelling segment.

Keep one observation/state/action/acknowledgement/outcome path. Consolidate
touched behavior into existing focused modules with timeline regressions.
Avoid wholesale rewrites and competing controllers. A failed experiment needs
a replay and changed input before a bounded retry, not erased history or a
character-name exception.

## Preserved History

The [previous roadmap](docs/history/ROADMAP_2026-09-08.md) retains the original
practical milestones, exit criteria, and subsequent cycles. The
[operating instructions](docs/OPERATIONS.md) retain commentary, fail-fast,
process, source-refresh, and local-only commit requirements.
