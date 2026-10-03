from dataclasses import replace

import pytest

from dd4tester.equipment import GearCatalog, ITEM_CURSED
from dd4tester.hunt_candidates import ObjectSource
from dd4tester.weapon_comparison import (
    WeaponComparison, plan_weapon_comparison, weapon_comparison_request,
)


PROMPT = "<666/666 hits 100/100 mana 434/482 move [Temple]> "
BRANCH = "a long, grey branch"
CLUB = "a large club"


def source_case():
    objects = {
        vnum: ObjectSource(
            vnum, "branch", BRANCH, item_type, values, 0,
            wear_flags=1 | ((1 << 13) if item_type == 5 else 0), level=15,
        )
        for vnum, item_type, values in (
            (6103, 1, (0, 0, 25, 0)),
            (6104, 5, (0, 2, 5, 7)),
            (6105, 13, (0, 0, 0, 0)),
        )
    }
    objects[1521] = ObjectSource(
        1521, "club", CLUB, 5, (0, 1, 2, 7), 0,
        wear_flags=1 | (1 << 13), level=3,
    )
    return GearCatalog(objects)


def plan(catalog, descriptions=(BRANCH,), **changes):
    options = dict(character_class="warrior", subclass=None, level=29)
    options.update(changes)
    return plan_weapon_comparison(catalog, catalog.objects[1521], descriptions, **options)


def record(vnum=1521, name=CLUB, item_type=5):
    return [{"slot": "wield", "wear_loc": 16, "vnum": vnum,
             "name": name, "item_type": item_type, "level": 15}]


def step(session, now=0, **changes):
    options = dict(
        now=now, equipment=record(), descriptions=(BRANCH,),
        catalog=source_case(), character_class="warrior", subclass=None,
        level=29, at_healer=True, in_combat=False,
    )
    options.update(changes)
    result = session.decide(**options)
    return result[0] if result else None


def start_comparison():
    session = WeaponComparison({**plan(source_case()), "level": 29, "boot_id": "boot"})
    assert step(session) == "eq all"
    session.observe(f"[weapon] {CLUB}\n" + PROMPT)
    assert step(session, 1) == "inventory"
    session.observe(f"Your backpack contains:\n{BRANCH}\nYou are carrying 2/40 items.\n" + PROMPT)
    assert step(session, 2) == "compare branch"
    return session


def test_comparison_is_read_only_until_exact_better_reply_and_verified_after_wield():
    session = start_comparison()
    session.observe(f"{BRANCH} looks better than {CLUB}.\n" + PROMPT)
    assert step(session, 3) == "wield branch"
    session.observe(f"You wield {BRANCH}.\n" + PROMPT)
    assert step(session, 4, equipment=record(6104, BRANCH)) == "eq all"
    session.observe(f"[weapon] {BRANCH}\n" + PROMPT)
    assert step(session, 5, equipment=record(6104, BRANCH)) is None
    assert session.stage == "verified"
    assert session.audit()["commands"] == 5
    assert session.audit()["boot_id"] == "boot"


@pytest.mark.parametrize("reply", [
    f"{BRANCH} looks worse than {CLUB}.",
    f"{BRANCH} and {CLUB} look about the same.",
    f"You can't compare {BRANCH} and {CLUB}.",
    "You aren't wearing anything comparable.", "You do not have that item.",
])
def test_rejected_comparison_never_equips_or_retries(reply):
    session = start_comparison()
    session.observe(reply + "\n" + PROMPT)
    assert step(session, 3) is None
    assert session.stage == "rejected"
    assert step(session, 20) is None
    assert session.commands == 3


@pytest.mark.parametrize("reply", [
    f"Someone says '{BRANCH} looks better than {CLUB}.'",
    f"{BRANCH} looks better than another club.",
    f"{BRANCH} looks better than {CLUB}",
])
def test_quoted_wrong_or_incomplete_reply_times_out(reply):
    session = start_comparison()
    session.observe(reply + "\n" + PROMPT)
    assert step(session, 3) is None
    assert step(session, 7) is None
    assert session.stage == "failed"
    assert session.commands == 3


def test_changed_primary_stops_comparison():
    session = start_comparison()
    session.observe(f"{BRANCH} looks better than {CLUB}.\n")
    assert step(session, 3, equipment=record(9999)) is None
    assert session.stage == "failed"


def test_healer_prompt_does_not_hide_split_comparison_reply():
    session = start_comparison()
    session.observe("\nThe Healer utters the word 'Lwo'.\n" + PROMPT)
    assert step(session, 2.3) is None
    session.observe("A long, grey branch looks better than ")
    assert step(session, 2.5) is None
    session.observe("a large club.\n" + PROMPT)
    assert step(session, 2.7) == "wield branch"
    session.observe(PROMPT + f"You wield {BRANCH}.\n" + PROMPT)
    assert step(session, 3, equipment=record(6104, BRANCH)) == "eq all"


def test_wrong_post_wield_vnum_is_not_verified_by_name():
    session = start_comparison()
    session.observe(f"{BRANCH} looks better than {CLUB}.\n")
    assert step(session, 3) == "wield branch"
    session.observe(f"You wield {BRANCH}.\n")
    assert step(session, 4) == "eq all"
    session.observe(f"[weapon] {BRANCH}\n" + PROMPT)
    assert step(session, 5, equipment=record(6103, BRANCH, 1)) is None
    assert session.stage == "failed"


@pytest.mark.parametrize("changes", [{"in_combat": True}, {"at_healer": False}])
def test_noncombat_healer_boundary_is_required(changes):
    session = WeaponComparison(plan(source_case()))
    assert step(session, **changes) is None
    assert session.stage == "failed"
    assert session.commands == 0


def test_equipment_requires_one_weapon_and_prompt_after_the_slot():
    session = WeaponComparison(plan(source_case()))
    assert step(session) == "eq all"
    session.observe(PROMPT + f"\n[weapon] {CLUB}\n")
    assert step(session, 1) is None
    session.observe(PROMPT)
    secondary = {**record(6104, BRANCH)[0], "slot": "secondary", "wear_loc": 18}
    assert step(session, 2, equipment=record() + [secondary]) is None
    assert session.stage == "failed"


def test_inventory_mismatch_does_not_send_compare():
    session = WeaponComparison(plan(source_case()))
    assert step(session) == "eq all"
    session.observe(f"[weapon] {CLUB}\n" + PROMPT)
    assert step(session, 1) == "inventory"
    session.observe("Your backpack contains:\nsomething else\n" + PROMPT)
    assert step(session, 2) is None
    assert session.stage == "failed"


@pytest.mark.parametrize("descriptions", [(BRANCH, BRANCH), (BRANCH, "unknown object")])
def test_unknown_or_duplicate_carried_items_prevent_planning(descriptions):
    assert plan(source_case(), descriptions) is None


def test_keyword_collision_across_other_carried_prototypes_prevents_planning():
    catalog = source_case()
    other = ObjectSource(999, "branchlet", "a twig", 13, (), 0)
    catalog = GearCatalog({**catalog.objects, 999: other})
    assert plan(catalog, (BRANCH, "a twig")) is None


def test_multiple_weapon_variants_cannot_be_resolved_by_comparison():
    catalog = source_case()
    catalog = GearCatalog({**catalog.objects, 6106: replace(catalog.objects[6104], vnum=6106)})
    assert plan(catalog) is None


def test_cursed_too_high_or_wrong_role_weapon_cannot_be_planned():
    catalog = source_case()
    assert plan(catalog, character_class="thief") is None
    assert plan(catalog, level=14) is None
    catalog = GearCatalog({**catalog.objects, 6104: replace(catalog.objects[6104], extra_flags=ITEM_CURSED)})
    assert plan(catalog) is None


def verified_comparison():
    return {**plan(source_case()), "level": 29, "boot_id": "boot",
            "stage": "verified", "failure": None, "commands": 5}


def test_verified_weapon_reversal_gets_one_fresh_comparison_with_old_evidence():
    previous = verified_comparison()
    request = weapon_comparison_request(plan(source_case()), previous, level=29, boot_id="boot")
    assert request["stage"] == "dispatched"
    assert request["restoration_of"]["stage"] == "verified"
    assert request["restoration_of"]["candidate_vnum"] == 6104
    assert previous == verified_comparison()
    assert weapon_comparison_request(plan(source_case()), request, level=29, boot_id="boot") is None
    request.update(stage="verified", commands=5, failure=None)
    assert weapon_comparison_request(plan(source_case()), request, level=29, boot_id="boot") is None


@pytest.mark.parametrize("changes", [
    {"stage": "dispatched"}, {"stage": "failed"}, {"stage": "rejected"},
    {"failure": "lost identity"}, {"commands": 4}, {"primary_vnum": 999},
    {"candidate_vnum": 999}, {"keyword": "wrong"}, {"restoration_of": None},
])
def test_restoration_needs_exact_successful_prior_comparison(changes):
    previous = {**verified_comparison(), **changes}
    assert weapon_comparison_request(plan(source_case()), previous, level=29, boot_id="boot") is None


def test_different_frontier_gets_ordinary_comparison_and_missing_plan_does_not():
    previous = verified_comparison()
    request = weapon_comparison_request(plan(source_case()), previous, level=30, boot_id="boot")
    assert request is not None and "restoration_of" not in request
    assert weapon_comparison_request(None, previous, level=29, boot_id="boot") is None
    assert weapon_comparison_request(plan(source_case()), previous, level=29, boot_id="") is None


def test_legacy_restoration_gets_one_fresh_recovery_identity_repair():
    previous = {**verified_comparison(), "restoration_of": verified_comparison()}
    request = weapon_comparison_request(plan(source_case()), previous, level=29, boot_id="boot")
    assert request["stage"] == "dispatched"
    assert request["recovery_identity_revision"] == 2
    assert request["recovery_identity_repair_of"] == previous
    assert weapon_comparison_request(plan(source_case()), request, level=29, boot_id="boot") is None
    request.update(stage="verified", failure=None, commands=5)
    assert weapon_comparison_request(plan(source_case()), request, level=29, boot_id="boot") is None


@pytest.mark.parametrize("changes", [
    {"commands": 4}, {"stage": "failed"}, {"candidate_vnum": 999},
    {"level": 28}, {"boot_id": "old"},
])
def test_legacy_recovery_repair_requires_matching_verified_original(changes):
    previous = {**verified_comparison(), "restoration_of": {**verified_comparison(), **changes}}
    assert weapon_comparison_request(plan(source_case()), previous, level=29, boot_id="boot") is None


def test_legacy_compare_timeout_can_refresh_once_without_reusing_reply():
    previous = {
        **verified_comparison(), "stage": "failed", "commands": 3,
        "failure": "weapon comparison timed out during compare",
        "restoration_of": verified_comparison(), "recovery_identity_revision": 2,
    }
    request = weapon_comparison_request(plan(source_case()), previous, level=29, boot_id="boot")
    assert request["prompt_repair_of"] == previous
    assert request["response_parser_revision"] == 2
    assert request["stage"] == "dispatched"
    request.update(stage="failed", commands=3, failure=previous["failure"])
    assert weapon_comparison_request(plan(source_case()), request, level=29, boot_id="boot") is None


def test_campaign_dispatches_restoration_before_other_healer_work(tmp_path, monkeypatch):
    from dd4tester import campaign
    from dd4tester.character import CharacterSpec
    from dd4tester.weapon_comparison import COMPARISON_KEY

    character = CharacterSpec.from_mapping({
        "name": "Testwarrior", "race": "dwarf", "gender": "neuter", "class": "warrior",
    })
    runner = campaign.CampaignRunner(
        campaign.CampaignSpec("comparison", tmp_path / "character.yaml", character),
        tmp_path / "campaign.yaml",
    )
    runner._gear_catalog = source_case()
    monkeypatch.setattr(runner, "_policy_without_learned_flight", lambda state: campaign._RETURN_HOME_POLICY)
    monkeypatch.setattr(campaign, "_has_campaign_food", lambda *a, **k: True)
    state = {
        "level": 29, "world_boot_id": "boot", "room_vnum": "3054",
        "hp": 100, "max_hp": 100, "move": 100, "max_move": 100,
        "mana": 100, "max_mana": 100, "campaign_has_weapon": True,
        "campaign_primary_weapon": CLUB, "campaign_worn_equipment": [CLUB],
        "equipment": record(), "inventory": [[{"short_desc": BRANCH}]],
        COMPARISON_KEY: verified_comparison(),
    }
    selected = runner._policy_for_state(state)
    assert selected.policy_id == "compare-carried-weapon"
    assert state[COMPARISON_KEY]["stage"] == "dispatched"
    assert state[COMPARISON_KEY]["restoration_of"]["stage"] == "verified"
