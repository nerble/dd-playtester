from dd4tester.loot_capacity import LootCapacityReply


def test_capacity_footer_must_follow_its_inventory_header() -> None:
    reply = LootCapacityReply()
    reply.begin("inventory", now=0)
    reply.observe("You are carrying 37/38 items.\nYour backpack contains:\n", now=1)
    assert reply.capacity() is None
    assert not reply.acknowledged()


def test_healer_prompt_and_fragmented_drop_wait_for_actual_acknowledgement() -> None:
    reply = LootCapacityReply()
    reply.begin("drop vine", now=10)
    reply.observe("The Healer utters the word 'Edahs'.\n\n", now=10.1)
    assert not reply.acknowledged()
    reply.observe("You drop an I.Q.", now=10.2)
    assert not reply.acknowledged()
    reply.observe(" Vine.\n", now=10.3)
    assert reply.acknowledged()
    assert not reply.expired(20)


def test_drop_acknowledgement_cannot_satisfy_sacrifice() -> None:
    reply = LootCapacityReply()
    reply.begin("drop vine", now=10)
    reply.observe("You drop an I.Q. Vine.\n", now=11)
    assert reply.acknowledged()
    reply.begin("sacrifice vine", now=12)
    assert not reply.acknowledged()
    reply.observe("You drop an I.Q. Vine.\n", now=12.1)
    assert not reply.acknowledged()
    reply.observe("You sacrifice an I.Q. Vine to God.\n", now=12.2)
    assert reply.acknowledged()


def test_inventory_needs_its_own_header_and_complete_capacity_line() -> None:
    reply = LootCapacityReply()
    reply.begin("inventory", now=10)
    reply.observe("The healer smiles.\n", now=10.1)
    assert reply.capacity() is None
    reply.observe("Your backpack contains:\na pie\nYou are carrying 37/", now=10.2)
    assert reply.capacity() is None
    reply.observe("38 items.\n", now=10.3)
    assert reply.capacity() == (37, 38)
    assert reply.acknowledged()


def test_capacity_line_without_inventory_header_is_not_a_receipt() -> None:
    reply = LootCapacityReply()
    reply.begin("inventory", now=10)
    reply.observe("You are carrying 37/38 items.\n", now=11)
    assert not reply.acknowledged()


def test_silent_reply_expires_and_late_acknowledgement_does_not_revive_it() -> None:
    reply = LootCapacityReply()
    reply.begin("drop vine", now=10)
    assert not reply.expired(14.99)
    assert reply.expired(15)
    reply.observe("You drop an I.Q. Vine.\n", now=15.01)
    assert reply.failure is not None
    assert not reply.acknowledged()


def test_acknowledgement_remains_stable_through_later_chatter() -> None:
    reply = LootCapacityReply()
    reply.begin("sacrifice vine", now=10)
    reply.observe("You sacrifice an I.Q. Vine to God.\n", now=11)
    reply.observe("Healer chatter\n" * 500, now=20)
    assert reply.acknowledged()
    assert reply.failure is None
