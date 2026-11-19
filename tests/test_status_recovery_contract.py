from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState
from dd4tester.status_recovery import SourceHealerRecovery


def poseidon_stop():
    return FieldHuntStop(
        (), "Poseidon", source_mobile_vnum=904, source_reset_room_vnum="946",
        source_specials=("spec_cast_mage",), exact_target=True,
        require_isolated=True, maximum_target_count=1,
        allow_healer_blindness_recovery=True,
        source_healer_recovery=SourceHealerRecovery(
            904, "946", ("spec_cast_mage",), 50,
            ("blindness", "weaken", "dispel magic", "energy drain"),
        ),
    )


def test_source_approved_mage_healer_return_reaches_live_status_gate():
    stop = poseidon_stop()
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", fastwalk_hunt_stops=(stop,),
        source_mobile_level_ranges_by_vnum={904: (46, 50)},
    )
    assert policy._source_status_recovery_issue(CharacterState(room_vnum="946"), stop) is None
    # Generic hunt stops use the current endpoint rather than the separate
    # required-loot reset-room field. The proof and live room still bind it.
    assert policy._source_status_recovery_issue(
        CharacterState(room_vnum="946"), replace(stop, source_reset_room_vnum=None),
    ) is None
    assert policy._source_status_recovery_issue(
        CharacterState(room_vnum="945"), stop
    ) is None


@pytest.mark.parametrize("change", [
    {"source_mobile_vnum": 905}, {"source_reset_room_vnum": "945"},
    {"source_specials": ("spec_cast_psionicist",)},
    {"require_isolated": False}, {"maximum_target_count": 2},
    {"source_healer_recovery": None}, {"allow_healer_blindness_recovery": False},
])
def test_healer_return_contract_does_not_widen_other_stops(change):
    stop = replace(poseidon_stop(), **change)
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", fastwalk_hunt_stops=(stop,),
        source_mobile_level_ranges_by_vnum={904: (46, 50), 905: (46, 50)},
    )
    # Psionics have their separate fatal-hazard gate; the shared proof itself
    # must never match them even if they have no blindness effect.
    if "psionicist" in str(change):
        assert not stop.source_healer_recovery.matches(
            mobile_vnum=904, reset_room="946", specials=stop.source_specials,
            source_level=50, effects=("blindness",),
        )
    else:
        assert policy._source_status_recovery_issue(
            CharacterState(room_vnum="946"), stop
        ) is None


def test_healer_return_contract_closes_on_live_room_or_level_change():
    proof = poseidon_stop().source_healer_recovery
    assert not proof.matches(mobile_vnum=904, reset_room="946",
                             specials=("spec_cast_mage",), source_level=51, effects=("blindness",))
    assert not proof.matches(mobile_vnum=904, reset_room="945",
                             specials=("spec_cast_mage",), source_level=50, effects=("blindness",))
