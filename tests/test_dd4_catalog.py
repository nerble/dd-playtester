from dd4tester.dd4_catalog import parse_character_catalog, parse_creation_sexes


SOURCE = r'''
const struct class_type class_table[MAX_CLASS] =
{
    {"Mag", "Mage", APPLY_INT, 1, 3018, 95, 18, 6, 6, 9, TRUE,
     "Necromancer", "Warlock", "Nec", "Wlk", {-1, 3, 1, 1, -1}},
    {"Thi", "Thief", APPLY_DEX, 1, 3028, 85, 18, 3, 9, 12, FALSE,
     "Ninja", "B. Hunter", "Nin", "Bou", {1, 1, -1, 3, -1}}
};

const struct sub_class_type sub_class_table[MAX_SUB_CLASS] =
{
    {"Non", "None", APPLY_STR, FALSE},
    {"Nec", "Necromancer", APPLY_WIS, TRUE},
    {"Wlk", "Warlock", APPLY_STR, TRUE},
    {"Nin", "Ninja", APPLY_CON, FALSE},
    {"Bou", "B. Hunter", APPLY_STR, FALSE}
};

const struct race_struct race_table[MAX_RACE] =
{
    {"None", "None", 0, 0, 0, 0, 0, 0, 0, 0, "NULL", "NULL", 0},
    {"Human", "Human", 0, 1, 0, 0, 0, 0, 0, 0,
     "Identify", "Detect Evil", CHAR_SIZE_MEDIUM},
    {"WildElf", "Wild-Elf", 1, -1, -2, 1, 2, 10, -10, 10,
     "Infravision", "Forage", CHAR_SIZE_MEDIUM}
};
'''


def test_parse_character_catalog_uses_dd4_table_order_and_relationships() -> None:
    catalog = parse_character_catalog(SOURCE, source="fixture const.c")

    assert [(race.name, race.creation_choice) for race in catalog.races] == [
        ("human", "a"),
        ("wild elf", "b"),
    ]
    assert [option.name for option in catalog.classes] == ["mage", "thief"]
    assert catalog.subclass_option("warlock").base_class == "mage"
    assert catalog.subclass_option("bounty hunter").base_class == "thief"
    assert catalog.subclass_option("B. Hunter").name == "bounty hunter"
    assert catalog.source == "fixture const.c"


def test_catalog_rejects_wrong_or_unknown_options() -> None:
    catalog = parse_character_catalog(SOURCE)

    try:
        catalog.class_name("paladin")
    except ValueError as exc:
        assert "unknown class" in str(exc)
        assert "mage" in str(exc)
    else:
        raise AssertionError("unknown class was accepted")


def test_parse_creation_sexes_reads_the_new_character_handler() -> None:
    source = r'''
case CON_GET_NEW_SEX:
    switch (argument[0])
    {
    case 'm':
    case 'M':
        ch->sex = SEX_MALE;
        break;
    case 'f':
    case 'F':
        ch->sex = SEX_FEMALE;
        break;
    case 'n':
    case 'N':
        ch->sex = SEX_NEUTRAL;
        break;
    }
    break;
case CON_DISPLAY_CLASS:
'''

    assert parse_creation_sexes(source) == ("male", "female", "neuter")
