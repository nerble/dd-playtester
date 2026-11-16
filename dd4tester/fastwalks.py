"""Official DD4 fastwalk routes expanded into individual MUD commands."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


_DIRECTIONS = {
    "n": "north",
    "e": "east",
    "s": "south",
    "w": "west",
    "u": "up",
    "d": "down",
}


@dataclass(frozen=True)
class FastwalkPostCommandAction:
    """A bounded item action to run after one exact route command succeeds."""

    after_command_index: int
    room_vnum: str
    preceding_command: str
    command: str
    accepted_preceding_responses: tuple[str, ...]
    acknowledgement_fragment: str
    verify_item_absent: str
    source_object_vnum: int | None = None


@dataclass(frozen=True)
class HuntPostCommandAction:
    """A verified item action to run after one exact hunt stop succeeds."""

    command: str
    room_vnum: str
    acknowledgement_fragment: str
    verify_item_absent: str
    source_object_vnum: int | None = None


@dataclass(frozen=True)
class Fastwalk:
    """A route copied from the official DD4 fastwalk list.

    Every listed route begins at Midgaard recall unless the source marks it
    otherwise. Routes are reference data until a live observation verifies an
    arrival room and a safe return.
    """

    name: str
    minimum_level: int
    maximum_level: int
    notation: str
    recall_after_loot: bool = False
    loot_container: str | None = None
    live_navigation_target: str | None = None
    live_navigation_entry_room: str | None = None
    live_navigation_start_index: int | None = None
    live_navigation_resume_index: int | None = None
    live_navigation_room_vnums: tuple[str, ...] = ()
    live_navigation_blocked_room_vnums: tuple[str, ...] = ()
    live_navigation_preferred_destinations: tuple[str, ...] = ()
    route_preflight_room_vnum: str | None = None
    route_preflight_command: str | None = None
    route_preflight_target: str | None = None
    # A route may need more than one exact source identity checked with
    # ``where``.  The legacy singular fields remain the first check for
    # fixed routes and older callers; generated routes can provide the full
    # ordered command/target pairs here.
    route_preflight_checks: tuple[tuple[str, str], ...] = ()
    route_preflight_hard_hazard: bool = False
    # Source-ranked routes set this only when the catalog proved one
    # non-deterministic attack program whose live location can be rechecked.
    route_preflight_retryable: bool = False
    # Normalized room names on this route where a probabilistic preflight
    # target is unsafe.  A live `where` result outside these rooms permits
    # the route to continue while the ordinary combat gates remain active.
    route_preflight_route_room_names: tuple[str, ...] = ()
    # Wandering route aggressors can move between a safe-origin locator and
    # the first path scan.  For source-ranked wandering hazards, any positive
    # `where` result in the current area therefore keeps the route closed.
    route_preflight_any_location_hazard: bool = False
    # `where` only searches the caller's current area. Source-ranked routes
    # therefore scan each adjacent destination the preflight mobile can reach.
    route_preflight_scan_room_vnums: tuple[str, ...] = ()
    route_hard_hazard_targets: tuple[str, ...] = ()
    # Generated source routes already carry their complete route-program
    # analysis. Fixed routes are marked after the campaign dispatcher audits
    # their source path so that the two policies cannot overwrite each other.
    route_source_program_audited: bool = False
    route_source_program_block_reason: str | None = None
    route_origin_recall_index: int = 0
    route_origin_room_vnum: int = 3001
    # Exact source room reached by a fixed route when a research profile
    # needs to build a bounded, area-local locator sweep from its endpoint.
    research_endpoint_room_vnum: int | None = None
    # Routes marked here must confirm active flight before the first move.
    requires_flight: bool = False
    # A route may be split at source-audited no-mob rooms for movement
    # recovery. Keep the complete outbound path available if recall fails
    # after the route has been shortened to its first leg.
    return_commands: tuple[str, ...] = ()
    # Some source maps contain one-way exits, so the outbound route cannot be
    # reversed even though an explicit source path home is available.
    direct_return_commands: tuple[str, ...] = ()
    # Only source-validated routes may reverse their closed-door commands.
    return_commands_allow_open: bool = False
    # Exact source identity for visibility-aware program preflight only.
    route_preflight_source_mobile_vnum: int | None = None
    # Exact, source-proven deep-below-band unarmed wanderers that a route
    # pre-entry scan may observe as transit noise.  This never authorizes
    # combat; the live scanner rechecks each identity and source contract.
    route_preflight_below_band_transit_mobile_vnums: tuple[int, ...] = ()
    # A small number of source-ranked routes have a separate, fully audited
    # set of scripted or special low-level mobiles on the approach.  These are
    # still route hazards, never targets; StarterPolicy keeps the live scan and
    # combat checks in force before allowing movement past them.
    route_preflight_deep_below_band_mobile_vnums: tuple[int, ...] = ()
    # Exact source aggressive mobiles audited as possible transit fighters.
    # Runtime still requires a singleton live identity and bounded output;
    # these VNUMs never turn a transit interruption into an XP target.
    route_aggressive_mobile_vnums: tuple[int, ...] = ()
    # Exact aggressive source mobiles whose update.c aggression check is
    # blocked only while fresh live invisibility remains confirmed.
    route_invisibility_source_mobile_vnums: tuple[int, ...] = ()
    # A source-ranked route may carry one borderline level-4 reset whose
    # maximum fuzzy level is below the useful-XP floor.  Runtime may finish
    # that exact mobile once, but only when this route explicitly registers
    # its source VNUM; ordinary routes never inherit the exception.
    route_bounded_borderline_source_mobile_vnums: tuple[int, ...] = ()
    # One exact source special may be tolerated as a bounded transit
    # interruption. The starter still requires its live GMCP VNUM; this never
    # authorizes an endpoint or progression kill.
    route_bounded_transit_special_mobile_vnums: tuple[int, ...] = ()
    # Keep those special-mobile exceptions tied to the exact audited route
    # rooms as well as to the source mobile identity.
    route_bounded_transit_special_room_vnums: tuple[str, ...] = ()
    # A source-ranked route may carry one exact plain aggressive mobile inside
    # the useful-XP band. Runtime still requires one isolated live VNUM,
    # source description, healthy player, and bounded source output before it
    # fights the interruption. These are route rooms, not endpoint rooms.
    route_allowed_plain_transit_mobile_vnums: tuple[int, ...] = ()
    route_allowed_plain_transit_room_vnums: tuple[str, ...] = ()
    # A Sanctuary-backed route may carry one exact armed, special-free
    # current-band mobile. Runtime requires active Sanctuary, exact live
    # identity, a singleton source reset, and the same bounded output proof
    # before it fights the interruption. These are route rooms, not endpoint
    # rooms, and never grant objective XP.
    route_allowed_armed_transit_mobile_vnums: tuple[int, ...] = ()
    route_allowed_armed_transit_room_vnums: tuple[str, ...] = ()
    # Exact source-identified current-band route interruptions must pass a
    # fresh live `consider` before the ordinary combat controller opens. This
    # includes unarmed fixed sentinels as well as armed wanderers.
    route_consider_transit_mobile_vnums: tuple[int, ...] = ()
    # Source-capacity research may inspect a live endpoint, but it must never
    # turn a transit interruption into a combat exception.
    no_combat_probe: bool = False
    # Exact noncombat quest transit only; runtime rechecks the whole purse.
    route_economic_special_mobile_vnums: tuple[int, ...] = ()
    route_economic_quest_identity: tuple[int, int, int] | None = None
    route_economic_max_copper: int | None = None
    # Ordinary XP travel has its own runtime purse gate, never a quest waiver.
    route_economic_hunt_mobile_vnums: tuple[int, ...] = ()
    # Population-only source proof for the ordinary XP economic gate.
    route_economic_hunt_allow_bounded_population: bool = False
    # A source-audited Sanctuary-backed endpoint may need a fresh staff
    # activation between separate, admitted plain transit fights.
    refresh_sanctuary_between_plain_transit_fights: bool = False
    # Do not enter that armed endpoint after the route has spent its
    # protection reserve on the transit fights.
    require_sanctuary_at_endpoint: bool = False
    post_command_actions: tuple[FastwalkPostCommandAction, ...] = ()
    # Source-ranked visibility routes may need a fresh affect for more than
    # the first room. The starter waits at the healer when an older affect is
    # shorter than this reserve, then activates the carried potion at recall.
    minimum_invisibility_duration: int | None = None

    @property
    def commands(self) -> tuple[str, ...]:
        return expand_fastwalk(self.notation)


@lru_cache(maxsize=1024)
def expand_fastwalk(notation: str) -> tuple[str, ...]:
    """Expand DD4 compact notation such as ``2s6e8n`` into commands."""
    commands: list[str] = []
    for raw_segment in notation.strip().casefold().split(";"):
        segment = raw_segment.strip().strip("{}")
        if not segment:
            raise ValueError(f"empty fastwalk segment in {notation!r}")
        if " " in segment:
            command, direction = segment.split(None, 1)
            if (
                command not in {"open", "unlock", "pick"}
                or direction not in _DIRECTIONS.values()
            ):
                raise ValueError(f"unsupported fastwalk command {segment!r}")
            commands.append(f"{command} {direction}")
            continue

        index = 0
        while index < len(segment):
            count_start = index
            while index < len(segment) and segment[index].isdigit():
                index += 1
            count = int(segment[count_start:index] or "1")
            if count < 1 or index == len(segment) or segment[index] not in _DIRECTIONS:
                raise ValueError(f"invalid compact fastwalk segment {segment!r}")
            commands.extend([_DIRECTIONS[segment[index]]] * count)
            index += 1
    return tuple(commands)


def routes_for_level(level: int) -> tuple[Fastwalk, ...]:
    """Return official routes whose suggested level bands include ``level``."""
    return tuple(
        route
        for route in FASTWALKS
        if route.minimum_level <= level <= route.maximum_level
    )


def route_named(name: str) -> Fastwalk:
    normalized = " ".join(name.casefold().replace("-", " ").split())
    for route in (*FASTWALKS, *MAP_ROUTES):
        if route.name == normalized:
            return route
    raise ValueError(f"unknown fastwalk route {name!r}")


# Source: https://dragons-domain.org/world/fastwalks/
FASTWALKS = (
    Fastwalk("thalos", 1, 30, "2s6e4s3w"),
    Fastwalk("arachnos", 2, 20, "2s13ws2wnwu2w"),
    Fastwalk("moria", 5, 15, "2s6e8n"),
    Fastwalk("dangerous neighbourhood", 5, 15, "2s3e2se"),
    Fastwalk("fleshmonger", 5, 12, "2s6e2s;open east;e"),
    Fastwalk("dragon cult", 5, 25, "3swn"),
    Fastwalk("ambush", 6, 16, "6s"),
    Fastwalk("sewer", 5, 30, "4sd"),
    Fastwalk("elemental canyon", 5, 30, "2s6e4s2es2eds2u"),
)


# Source-backed hunt routes omitted from show-fastwalks, which lists only the
# site's official fastwalks.
MAP_ROUTES = (
    Fastwalk(
        "olympus apollo consider",
        39,
        39,
        "s;2u;n;2u;2n;w",
        recall_after_loot=True,
        research_endpoint_room_vnum=926,
        requires_flight=True,
    ),
    Fastwalk(
        "vampire catacombs bevan",
        25,
        40,
        "6sw2swsw4se;open south;s2w5s2w3s2w5swnw2swsd2s2w;"
        "4e2n8e4s2esenes6e;4ne2n",
        recall_after_loot=True,
    ),
    Fastwalk("foundry", 1, 6, "2s3w4ne2d2n", recall_after_loot=True),
    Fastwalk(
        "circus midget",
        3,
        6,
        "2s3e6s3es",
        recall_after_loot=True,
        loot_container="purse",
    ),
    Fastwalk(
        "circus bearded lady",
        3,
        10,
        "2s3e6s2e",
        recall_after_loot=True,
    ),
    Fastwalk(
        "circus strongman",
        5,
        12,
        "2s3e6ses",
        recall_after_loot=True,
    ),
    Fastwalk(
        "circus illusionist",
        5,
        12,
        "2s3e6s3e",
        recall_after_loot=True,
    ),
    Fastwalk(
        "gnome mine",
        5,
        10,
        "2s5es6ene",
        recall_after_loot=True,
    ),
    Fastwalk(
        "gnome guard hut",
        7,
        10,
        "2s5es2e3s2w",
        recall_after_loot=True,
    ),
    Fastwalk(
        "gnome small troll",
        7,
        10,
        "2s5es2e5sen",
        recall_after_loot=True,
    ),
    Fastwalk(
        "gnome treasury",
        13,
        15,
        "2s5es6en3e3s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "shire dwarven prince",
        17,
        20,
        "2s5w4n2w5nw",
        recall_after_loot=True,
    ),
    Fastwalk(
        "shire thain",
        17,
        20,
        "2s5w4n5e",
        recall_after_loot=True,
    ),
    Fastwalk(
        "shire elven wizard",
        17,
        20,
        "2s5w4n5w",
        recall_after_loot=True,
    ),
    Fastwalk(
        "argent bandit leader",
        17,
        20,
        "2s6e4s2es2ed2e5n5es",
        recall_after_loot=True,
    ),
    Fastwalk(
        "pyramid ali baba",
        18,
        20,
        "3s;2e;2s;9e;ew2n2e;e;u;n;e;u;open down;2d;4e;n",
        recall_after_loot=True,
        live_navigation_target="2600",
        live_navigation_start_index=16,
        live_navigation_resume_index=22,
        live_navigation_room_vnums=(
            "5007",
            "5024",
            "5025",
            "5026",
            "5027",
            "5028",
            "5029",
            "5030",
            "5031",
            "5032",
            "5056",
            "2600",
        ),
        live_navigation_blocked_room_vnums=("5028",),
        live_navigation_preferred_destinations=("5056",),
    ),
    Fastwalk(
        "solace lord doom",
        18,
        20,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;w;9n;open west;w;u;2w;2n;3e;open south;s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "solace magnus",
        19,
        20,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;w;9n;open west;w;u;2w;2n;2e;open south;s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "foundry captain",
        7,
        7,
        "2s3w4ne2d2n;w;open south;s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "plains aruncus",
        13,
        18,
        "2s4w3n2e5nw",
        recall_after_loot=True,
    ),
    Fastwalk(
        "dwarven workers",
        13,
        15,
        "2s6edn",
        recall_after_loot=True,
    ),
    Fastwalk(
        "dwarven nobleman",
        13,
        18,
        (
            "6sw2swsw2sw2s;open south;6s2w3s2w2s4en;"
            "open east;e3n2en"
        ),
        recall_after_loot=True,
        route_preflight_room_vnum="3505",
        route_preflight_command="where goblin lieutenant",
        route_preflight_target="goblin lieutenant",
        route_preflight_hard_hazard=True,
        route_hard_hazard_targets=(
            "dark horseman",
            "wyvern",
        ),
    ),
    Fastwalk(
        "dwarven servant",
        17,
        18,
        (
            "6sw2swsw2sw2s;open south;6s2w3s2w2s4en;"
            "open east;e3n2e2nw"
        ),
        recall_after_loot=True,
    ),
    Fastwalk(
        "mahn tor rock toads",
        14,
        18,
        "2s6e4s2es2ed3ne3se2swsw",
        recall_after_loot=True,
    ),
    Fastwalk(
        "mirror realm watchman",
        16,
        20,
        "2s4w3n2e3ne3n2e2n;open north;3nw",
        recall_after_loot=True,
    ),
    Fastwalk(
        "crystalmir white stag",
        16,
        20,
        "6sw2swsw2sw2s;open south;6s2w3s2w5swnw2swsd2w2n3w",
        recall_after_loot=True,
        route_hard_hazard_targets=("Fewmaster Toede",),
    ),
    Fastwalk(
        "shadow keep soldier",
        16,
        20,
        "6sw2s2ws3wn2wse",
        recall_after_loot=True,
    ),
    Fastwalk(
        "highland keeper",
        17,
        20,
        "2s6e8ne2ne6n2dnese4n6w",
        recall_after_loot=True,
    ),
    Fastwalk(
        "galaxy white dwarf",
        17,
        20,
        "2s13ws2w2sws3wnwn",
        recall_after_loot=True,
        route_preflight_room_vnum="1300",
        route_preflight_command="where shadow guardian",
        route_preflight_target="shadow guardian",
        route_preflight_hard_hazard=True,
    ),
    Fastwalk(
        "galaxy red supergiant",
        17,
        20,
        "2s13ws2w2sws3wnwn",
        recall_after_loot=True,
        route_preflight_room_vnum="1300",
        route_preflight_command="where shadow guardian",
        route_preflight_target="shadow guardian",
        route_preflight_hard_hazard=True,
    ),
    Fastwalk(
        "galaxy horsehead nebula",
        18,
        20,
        "2s13ws2w2sws3wnwn",
        recall_after_loot=True,
        route_preflight_room_vnum="1300",
        route_preflight_command="where shadow guardian",
        route_preflight_target="shadow guardian",
        route_preflight_hard_hazard=True,
    ),
    Fastwalk(
        "hightower jailor",
        17,
        20,
        "2s13ws2w2sws3wnwn",
        recall_after_loot=True,
        route_preflight_room_vnum="1300",
        route_preflight_command="where shadow guardian",
        route_preflight_target="shadow guardian",
        route_preflight_hard_hazard=True,
    ),
    Fastwalk(
        "mirror realm gardener",
        21,
        25,
        "2s4w3n2e3ne3n2e2n;open north;3ne2d;open east;e2n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "mirror realm fame recovery",
        24,
        26,
        "2s4w3n2e3ne3n2e2n;open north;3nw2d;open west;w2s2ws",
        recall_after_loot=True,
    ),
    Fastwalk(
        "circus fame recovery",
        24,
        26,
        "2s3e4s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "lotus temple fame recovery",
        24,
        26,
        "6sw2swsw2sw2s;open south;6s2w3s2w5swnw2swsd3wnwnwn2w;"
        "open south;5s;open south;2sene2swd",
        recall_after_loot=True,
    ),
    Fastwalk(
        "mirror realm guardian",
        26,
        30,
        "2s4w3n2e3ne3n2e2n;open north;6n;open north;6n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "shire battle master",
        26,
        30,
        "2s5w4n3ese",
        recall_after_loot=True,
    ),
    Fastwalk(
        "minotaur gatekeeper",
        31,
        35,
        "2s6e4s2eseed3ne3se2sw3sd4se2s2u;open south;ses2e",
        recall_after_loot=True,
        live_navigation_target="2360",
        live_navigation_entry_room="2351",
        live_navigation_start_index=37,
        live_navigation_resume_index=40,
        live_navigation_room_vnums=(
            "2351",
            "2352",
            "2354",
            "2355",
            "2356",
            "2357",
            "2358",
            "2359",
            "2360",
        ),
        live_navigation_preferred_destinations=("2358",),
    ),
    Fastwalk(
        "galaxy cancer",
        31,
        35,
        "2s13ws2w2sws3wnw3n2edne2nuw",
        recall_after_loot=True,
        route_preflight_room_vnum="1300",
        route_preflight_command="where shadow guardian",
        route_preflight_target="shadow guardian",
        route_preflight_hard_hazard=True,
    ),
    Fastwalk(
        "mirror realm jerry garcia",
        36,
        40,
        # Use the source-shortest east-gate approach.  The older west-side
        # prefix crossed Common Square, where the low-level Drunk can greet
        # the character and draw a cityguard into an otherwise harmless trip.
        "2s4e3n2w3ne3n2e5nw2d5wswu2e",
        recall_after_loot=True,
    ),
    Fastwalk(
        "mirror realm caerlin",
        35,
        40,
        "2s4e3n2w3ne3n2e5nw2d5w",
        recall_after_loot=True,
        research_endpoint_room_vnum=19068,
        return_commands_allow_open=True,
    ),
    Fastwalk(
        "mirror realm caerlin watchtowers",
        35,
        40,
        "2s4e3n2w3ne3n2e5n",
        recall_after_loot=True,
        research_endpoint_room_vnum=19008,
        route_economic_hunt_mobile_vnums=(19036,),
    ),
    Fastwalk(
        "mirror realm caerlin face",
        35,
        40,
        "2s4e3n2w3ne3n2e2n",
        recall_after_loot=True,
        research_endpoint_room_vnum=19005,
        route_economic_hunt_mobile_vnums=(19036,),
    ),
    Fastwalk("pit official", 41, 45, "nund", recall_after_loot=True),
    Fastwalk(
        "dwarven home chess dwarf",
        45,
        50,
        "6sw2swsw2sw2s;open south;6s2w3s2w2s4en;open east;e3n5e2s2es",
        recall_after_loot=True,
        research_endpoint_room_vnum=20530,
    ),
    Fastwalk(
        "mirror realm storn",
        45,
        50,
        "2s;4w;3n;2e;3n;e;3n;2e;2n;open north;3n;e;2d;open east;5e;2s",
        recall_after_loot=True,
        research_endpoint_room_vnum=19114,
    ),
    Fastwalk(
        "mirror realm master dunn",
        45,
        50,
        "2s4e3n2w3ne3n2e5nw2d5wswu2e;2wdes",
        recall_after_loot=True,
        research_endpoint_room_vnum=19073,
    ),
    Fastwalk(
        "darkwood strange mist",
        51,
        55,
        "2s6e4s2es2ed4n3w2nwnw4n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "dwarven home gambler",
        51,
        55,
        "6sw2swsw2sw2s;open south;6s2w3s2w2s4en;open east;e3n5e2s3e",
        recall_after_loot=True,
        research_endpoint_room_vnum=20531,
    ),
    Fastwalk(
        "dwarven home master",
        56,
        60,
        "6sw2swsw2sw2s;open south;6s2w3s2w2s4en;open east;e3n5e3n",
        recall_after_loot=True,
        research_endpoint_room_vnum=20537,
    ),
    Fastwalk(
        "vampire hive wounded vampire",
        61,
        65,
        "6sw2swsw2sw2s;open south;6s2w3s2w5swnw2swsdw7n2e3n;open down;d4n;open down;d7se",
        recall_after_loot=True,
    ),
    Fastwalk(
        "tabernacle hulking beast",
        66,
        70,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;3w;n;10w;2u;3e;3s;e;w;s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "pirates seas rastafarians",
        71,
        75,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;3w;n;10w;4n;3e;2s;open down;d;2w;3s;e;2n;6w;n;e;n;e;n;e;6n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "ghost town crypt thing",
        76,
        76,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;3w;n;10w;4n;3e;2s;open down;d;2w;3s;e;2n;6w;n;w;17n;2w;3n;2w;2n;3e;2n;e;s;e;2n;w;4n;w;8n;3w;open west;3w;u;e;open north;n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "ghost town retriever",
        77,
        80,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;3w;n;10w;4n;3e;2s;open down;d;2w;3s;e;2n;6w;n;w;17n;2w;3n;2w;2n;3e;2n;e;s;e;2n;w;4n;w;8n;3w;open west;w;open north;n",
        recall_after_loot=True,
    ),
)
