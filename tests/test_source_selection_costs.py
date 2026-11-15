from types import SimpleNamespace

import pytest

import dd4tester.campaign as campaign


@pytest.mark.parametrize("check", [
    campaign._source_ranked_irmugar_mage_candidate_shape_allowed,
    campaign._source_ranked_white_lotus_mage_candidate_shape_allowed,
])
def test_exact_shape_rejects_other_targets_before_reading_world(check):
    candidate = SimpleNamespace(mobile_vnum=-1, room_vnum=-1)
    assert check(candidate, SimpleNamespace()) is False
