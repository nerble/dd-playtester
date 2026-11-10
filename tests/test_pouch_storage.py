from dataclasses import replace

from dd4tester.equipment import GearCatalog, ITEM_CURSED, ITEM_NODROP
from dd4tester.hunt_candidates import ITEM_PILL, ObjectSource
from dd4tester.pouch_storage import HealerPouchStorage, empty_pouch_storage_plan


PROMPT = "<743/743 hits 290/290 mana 502/502 move [Midgaard]> "


def _catalog():
    pouch = ObjectSource(3370, "beltpouch belt pouch", "a small leather pouch", 15,
                         (9, 0, -1, 0), 1, weight=1)
    first = ObjectSource(311, "potion clear", "a clear potion", 10, (20,), 1, weight=2)
    second = ObjectSource(4442, "clear potion", "a clear potion", 10, (30,), 1,
                          weight=3, extra_flags=ITEM_NODROP)
    return GearCatalog({item.vnum: item for item in (pouch, first, second)})


def _plan(catalog=None):
    return empty_pouch_storage_plan(
        ["a clear potion", "a clear potion"],
        [{"slot": "pouch", "vnum": 3370, "name": "a small leather pouch"}],
        catalog or _catalog(),
    )


def test_storage_does_not_infer_effects_from_ambiguous_potion() -> None:
    plan = _plan()
    assert plan.potion_vnums == (311, 4442)
    assert plan.quantity == 2
    assert plan.potion_keyword == "clear"


def test_storage_requires_exact_worn_container_identity() -> None:
    assert empty_pouch_storage_plan(["a clear potion"],
        [{"slot": "pouch", "name": "a small leather pouch"}], _catalog()) is None


def test_storage_rejects_cursed_candidate_and_keyword_collision() -> None:
    catalog = _catalog()
    catalog.objects[311] = replace(catalog.objects[311], extra_flags=ITEM_CURSED)
    assert _plan(GearCatalog(catalog.objects)) is None
    catalog = _catalog()
    conflict = ObjectSource(1, "clear crystal", "a clear crystal", 8, (), 1)
    catalog = GearCatalog({**catalog.objects, 1: conflict})
    assert empty_pouch_storage_plan(["a clear potion", "a clear crystal"],
        [{"slot": "pouch", "vnum": 3370, "name": "a small leather pouch"}], catalog) is None


def test_storage_never_counts_healer_chatter_as_empty_pouch() -> None:
    storage = HealerPouchStorage()
    assert storage.begin(_plan(), 39, now=0) == "look in beltpouch"
    storage.observe("The Healer smiles.\n" + PROMPT, now=1)
    assert storage.next_command(39, 38, now=1) is None
    assert storage.phase == "audit"
    storage.observe("A small leather pouch contains:\nNothing.\n" + PROMPT, now=2)
    assert storage.next_command(39, 38, now=2) == "put clear beltpouch"


def test_storage_preserves_existing_pouch_contents() -> None:
    storage = HealerPouchStorage()
    storage.begin(_plan(), 39, now=0)
    storage.observe("A small leather pouch contains:\na purple potion\n" + PROMPT, now=1)
    assert storage.next_command(39, 38, now=1) is None
    assert storage.phase == "unavailable" and storage.packed == 0


def test_storage_requires_each_acknowledgement_and_fresh_capacity() -> None:
    storage = HealerPouchStorage()
    storage.begin(_plan(), 39, now=0)
    storage.observe("A small leather pouch contains:\nNothing.\n" + PROMPT, now=1)
    assert storage.next_command(39, 38, now=1) == "put clear beltpouch"
    storage.observe("The Healer smiles.\n" + PROMPT, now=2)
    assert storage.next_command(39, 38, now=2) is None
    storage.observe("You put a clear potion in a small leather pouch.\n", now=2.5)
    assert storage.next_command(38, 38, now=2.5) == "put clear beltpouch"
    storage.observe("You put a clear potion in a small leather pouch.\n", now=3)
    assert storage.next_command(37, 38, now=3) == "inventory"
    storage.observe("Your backpack contains:\nYou are carrying 37/38 items.\n", now=4)
    assert storage.next_command(38, 38, now=4) is None
    assert storage.pending
    assert storage.next_command(37, 38, now=4.1) is None
    assert storage.receipt()["status"] == "complete"
    assert storage.receipt()["storage_only"]


def test_storage_can_free_capacity_with_duplicate_source_pills() -> None:
    pouch = ObjectSource(
        3370, "beltpouch belt pouch", "a small leather pouch", 15,
        (9, 0, -1, 0), 1, weight=1,
    )
    beads = ObjectSource(
        10721, "enchanted prayer beads", "enchanted prayer beads", ITEM_PILL,
        (1, 0, 0, 0), 1, weight=1, extra_flags=64,
    )
    catalog = GearCatalog({pouch.vnum: pouch, beads.vnum: beads})
    plan = empty_pouch_storage_plan(
        ["enchanted prayer beads", "enchanted prayer beads"],
        [{"slot": "pouch", "vnum": pouch.vnum, "name": pouch.short_description}],
        catalog,
    )

    assert plan is not None
    assert plan.potion_keyword == "enchanted"
    assert plan.potion_vnums == (beads.vnum,)
    assert plan.quantity == 2

    storage = HealerPouchStorage()
    assert storage.begin(plan, 41, now=0) == "look in beltpouch"
    storage.observe("A small leather pouch contains:\nNothing.\n" + PROMPT, now=1)
    assert storage.next_command(41, 41, now=1) == "put enchanted beltpouch"
    storage.observe("You put enchanted prayer beads in a small leather pouch.\n", now=2)
    assert storage.next_command(40, 41, now=2) == "put enchanted beltpouch"
    storage.observe("You put enchanted prayer beads in a small leather pouch.\n", now=3)
    assert storage.next_command(39, 41, now=3) == "inventory"
    storage.observe("Your backpack contains:\nYou are carrying 39/41 items.\n", now=4)
    assert storage.next_command(39, 41, now=4.1) is None
    assert storage.receipt()["status"] == "complete"


def test_storage_capacity_failure_and_late_reply_stay_visible() -> None:
    storage = HealerPouchStorage()
    storage.begin(_plan(), 39, now=0)
    storage.observe("A small leather pouch contains:\nNothing.\n" + PROMPT, now=5)
    assert storage.phase == "failed"
    assert "five seconds" in storage.failure
    assert storage.next_command(39, 38, now=5) is None


def test_storage_release_refusal_is_bounded_without_counting_capacity() -> None:
    storage = HealerPouchStorage()
    storage.begin(_plan(), 39, now=0)
    storage.observe("A small leather pouch contains:\nNothing.\n" + PROMPT, now=1)
    storage.next_command(39, 38, now=1)
    storage.observe("You can't let go of it.\n", now=2)
    assert storage.next_command(39, 38, now=2) is None
    assert storage.phase == "unavailable" and storage.packed == 0
    assert storage.failure is None
