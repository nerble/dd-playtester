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


def test_remove_acknowledgement_accepts_dd4_stop_using_reply() -> None:
    reply = LootCapacityReply()
    reply.begin("remove spiked", now=10)
    reply.observe("You stop using a spiked key.\n", now=11)
    assert reply.acknowledged()
    assert reply.failure is None


def test_eating_requires_a_confirmed_consumption_and_rejects_fullness() -> None:
    reply = LootCapacityReply()
    reply.begin("eat pie", now=10)
    reply.observe("You are full.\n", now=11)
    assert reply.failure is not None
    assert not reply.acknowledged()

    reply.begin("eat pie", now=12)
    reply.observe("You eat a big pot pie.\nYou are full.\n", now=13)
    assert reply.acknowledged()
    assert reply.failure is None


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


def test_inventory_items_are_available_only_from_a_complete_listing() -> None:
    reply = LootCapacityReply()
    reply.begin("inventory", now=10)
    reply.observe(
        "Your backpack contains:\n"
        "a deep green key\n"
        "(2) a small potion\n"
        "You are carrying 37/38 items.\n",
        now=11,
    )

    assert reply.inventory_items() == {
        "a deep green key": 1,
        "a small potion": 2,
    }

    reply.begin("inventory", now=12)
    reply.observe("Your backpack contains:\na deep green key\n", now=13)
    assert reply.inventory_items() is None


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
