from dd4tester.hunt_candidates import HuntCandidate
from dd4tester.money import route_notation, select_money_targets


def _candidate(
    target: str,
    *,
    score: float,
    loot: tuple[str, ...],
    boot_kills: int = 0,
    instance_limit: int = 1,
    status: str = "caution",
    area_file: str = "foundry.are",
) -> HuntCandidate:
    return HuntCandidate(
        status=status,
        score=score,
        area_file=area_file,
        mobile_vnum=1,
        target=target,
        target_keyword=target.casefold(),
        level=3,
        room_vnum=100,
        room_name="Foundry",
        route=("south",),
        source_spawn_limit=instance_limit,
        room_spawn_count=1,
        boot_kills=boot_kills,
        loot=loot,
        source_value=0,
        contained_coins=0,
        hazards=(),
    )


def test_money_targets_do_not_treat_boot_kills_as_a_spawn_limit() -> None:
    candidates = [
        _candidate("exhausted", score=100, loot=("cap",), boot_kills=1),
        _candidate("dangerous", score=99, loot=("rod",), status="reject"),
        _candidate("available", score=50, loot=("jerkin",)),
    ]

    selected = select_money_targets(candidates, trip_limit=3)

    assert [candidate.target for candidate in selected] == ["exhausted", "available"]


def test_money_targets_favor_varied_drops_before_raw_score() -> None:
    candidates = [
        _candidate("first", score=100, loot=("cap", "rod")),
        _candidate("duplicate", score=90, loot=("cap",)),
        _candidate("varied", score=80, loot=("boots", "jerkin")),
    ]

    selected = select_money_targets(candidates, trip_limit=2)

    assert [candidate.target for candidate in selected] == ["first", "varied"]


def test_money_targets_are_limited_to_the_verified_area() -> None:
    candidates = [
        _candidate("other", score=200, loot=("treasure",), area_file="other.are"),
        _candidate("foundry", score=20, loot=("cap",)),
    ]

    selected = select_money_targets(candidates, trip_limit=1)

    assert [candidate.target for candidate in selected] == ["foundry"]


def test_money_targets_require_a_compatible_safe_buyer() -> None:
    candidates = [
        _candidate("masonry", score=100, loot=("a chunk of broken masonry",)),
        _candidate("armour", score=20, loot=("a leather jerkin",)),
    ]

    selected = select_money_targets(candidates, trip_limit=2)

    assert [candidate.target for candidate in selected] == ["armour"]


def test_source_route_is_converted_to_fastwalk_notation() -> None:
    assert route_notation(("south", "west", "open south", "down")) == (
        "s;w;open south;d"
    )
