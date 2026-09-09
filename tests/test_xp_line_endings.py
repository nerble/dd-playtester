import json
from pathlib import Path

import pytest

from dd4tester.observations import ObservationParser
from dd4tester.state import CharacterState


def worth(xp):
    return "Char.Worth " + json.dumps({
        "level": "8", "xp": str(xp), "maxxp": "31700",
        "xptnl": str(31700 - xp), "xplvl": "6850",
    })


def loss_response(ending):
    return ending.join([
        "You flee from combat! You lose 68 exp.",
        "However, you damaged your opponent sufficiently for 15 experience.",
        "", "<107/113 hits 212/324 mana 138/220 move [Moria]> ",
    ])


@pytest.mark.parametrize("ending", ["\n", "\r", "\r\n", "\n\r"])
@pytest.mark.parametrize("fragmented", [False, True])
@pytest.mark.parametrize("order", ["gmcp-first", "text-first", "text-only"])
def test_run_12816_flee_refund_and_worth_reconcile_once(ending, fragmented, order):
    parser = ObservationParser()
    state = CharacterState(level=8, xp=28868, max_xp=31700, xp_to_next_level=2832,
                           progress_source="gmcp")
    if order == "gmcp-first":
        for event in parser.feed_gmcp(worth(28815)):
            state.apply(event)
    text = loss_response(ending)
    events = []
    for chunk in text if fragmented else [text]:
        events.extend(parser.feed_text(chunk))
    events.extend(parser.flush_text())
    losses = [event for event in events if event.type == "experience_lost"]
    assert len(losses) == 1 and losses[0].data["partial_xp"] == 15
    for event in events:
        state.apply(event)
    if order == "text-first":
        for event in parser.feed_gmcp(worth(28815)):
            state.apply(event)
    assert state.xp == 28815 and state.xp_to_next_level == 2885
    assert state.xp_loss_observed and state.xp_loss_total == 68


def test_second_gmcp_first_loss_in_one_connection_is_not_subtracted_twice():
    parser = ObservationParser()
    state = CharacterState(level=8, xp=28868, max_xp=31700, xp_to_next_level=2832,
                           progress_source="gmcp")
    for xp in [28815, 28762]:
        for event in parser.feed_gmcp(worth(xp)) + parser.feed_text(loss_response("\n\r")):
            state.apply(event)
        assert state.xp == xp and state.xp_to_next_level == 31700 - xp
    assert state.xp_loss_total == 136


@pytest.mark.parametrize("ending", ["\n", "\r", "\r\n", "\n\r"])
def test_line_break_pairs_preserve_actual_blank_lines(ending):
    parser = ObservationParser()
    text = "one" + ending * 2 + "two" + ending
    assert "".join(parser._normalize_line_breaks(char) for char in text) == "one\n\ntwo\n"


def test_newline_pair_state_is_connection_local():
    parser = ObservationParser()
    assert parser._normalize_line_breaks("one\n") == "one\n"
    parser.reset_connection()
    assert parser._normalize_line_breaks("\rtwo") == "\ntwo"


@pytest.mark.parametrize("fragmented", [False, True])
@pytest.mark.parametrize("order", ["gmcp-first", "text-first", "text-only"])
def test_live_12818_flee_refund_fixture(fragmented, order):
    fixture = json.loads(
        (Path(__file__).parent / "fixtures" / "dd4_flee_refund.json").read_text(
            encoding="utf-8"
        )
    )
    parser = ObservationParser()
    state = CharacterState.from_dict(fixture["initial"])
    if order == "gmcp-first":
        for event in parser.feed_gmcp(fixture["gmcp"]):
            state.apply(event)
    events = []
    text = fixture["text"]
    for chunk in text if fragmented else [text]:
        for event in parser.feed_text(chunk):
            events.append(event)
            state.apply(event)
    for event in parser.flush_text():
        events.append(event)
        state.apply(event)
    if order == "text-first":
        for event in parser.feed_gmcp(fixture["gmcp"]):
            state.apply(event)
    expected = fixture["expected"]
    losses = [event for event in events if event.type == "experience_lost"]
    assert len(losses) == 1
    assert losses[0].data["partial_xp"] == expected["partial_xp"]
    assert state.xp == expected["xp"]
    assert state.xp_to_next_level == expected["xp_to_next_level"]
    assert state.xp_loss_total == expected["gross_loss"]
    assert state.xp_loss_observed
