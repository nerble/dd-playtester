import json

import pytest

from dd4tester.report import _nested_strings, _objective_outcome


def _context(quantity=2):
    return {"objective": {
        "level": 100,
        "fastwalk_route": "source food reserve",
        "fastwalk_hunt_stop_boundaries": [{"required_items": ["some grain"] * quantity}],
    }}


def _outcome(inventory, *, quantity=2, **objective):
    context = _context(quantity)
    context["objective"].update(objective)
    return _objective_outcome(context, {"inventory": inventory, "level": 32}, [], [],
                              scenario_name="fastwalk-source food reserve:Testbot")


def test_raw_dd4_colour_codes_preserve_two_distinct_inventory_portions() -> None:
    inventory = ('[ [ {"quan":"1","short_desc":"[#25124] some grain"}, '
                 '{"quan":"1","short_desc":"some grain"}, '
                 '{"quan":"3","short_desc":"\x1b[38;5;121m(Glowing)\x1b[0m an I.Q. Vine"} ] ]')
    assert len(_nested_strings(inventory)) == 5
    assert _outcome(inventory) == "achieved"


def test_escaped_colour_codes_and_numeric_quantity_keep_distinct_counts() -> None:
    inventory = json.dumps([[{"quan": "2", "short_desc": "\x1b[32msome grain\x1b[0m"}]])
    assert _outcome(inventory) == "achieved"
    assert _outcome(inventory, quantity=3) == "not_achieved"


def test_one_portion_does_not_satisfy_two_requirements_after_colour_cleanup() -> None:
    inventory = '[ {"quan":"1","short_desc":"\x1b[32msome grain\x1b[0m"} ]'
    assert _outcome(inventory) == "not_achieved"


def test_unterminated_or_unquoted_inventory_is_not_item_evidence() -> None:
    for inventory in ('[{"quan":"2","short_desc":"some grain"}',
                      '[{quan:2,short_desc:"some grain"}]',
                      '[{"quan":"2","short_desc":"some grain\x1b[32'):
        assert _nested_strings(inventory) == []
        assert _outcome(inventory, quantity=1) == "not_achieved"


def test_item_selector_prefix_is_plain_single_item_evidence_not_json() -> None:
    assert _nested_strings("[#25124] some grain") == ["[#25124] some grain"]
    assert _outcome(["[#25124] some grain"], quantity=1) == "achieved"
    assert _outcome(["[#25124] some grain"]) == "not_achieved"


def test_inventory_confirmation_never_overrides_explicit_level_requirement() -> None:
    inventory = '[{"quan":"2","short_desc":"\x1b[32msome grain\x1b[0m"}]'
    assert _outcome(inventory, required_level=33) == "not_achieved"


@pytest.mark.parametrize("quantity", [0, "0"])
def test_quantity_zero_is_not_inventory_evidence(quantity) -> None:
    # A zero quantity must not be replaced by the default quantity of one.
    assert _outcome([{"quan": quantity, "short_desc": "some grain"}], quantity=1) == "not_achieved"
