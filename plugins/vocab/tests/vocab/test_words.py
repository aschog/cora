from cora.plugins.vocab.words import Pair, pairs_in

TABLE = """# English — Einheit 3

| Deutsch | English |
| --- | --- |
| Hilfe | help |
| Haus | house |
"""

# What the reading of a screenshot actually saves: numbered lines, an em dash, and the
# odd slip the reader left in.
READ = """1. Apple — Apfel
2. Book — Buch
3. Cat— Katze
9, Water — Wasser
"""


def test_a_table_gives_its_rows_and_its_column_names() -> None:
    assert pairs_in(TABLE, "einheit-3.md") == (
        Pair(
            left="Hilfe",
            right="help",
            sides=("Deutsch", "English"),
            source="einheit-3.md",
        ),
        Pair(
            left="Haus",
            right="house",
            sides=("Deutsch", "English"),
            source="einheit-3.md",
        ),
    )


def test_a_list_read_out_of_a_screenshot_gives_its_pairs() -> None:
    """Numbered, em-dashed, and typed by nobody: this is what the reading saves, and it
    is a list as much as a table is."""
    read = pairs_in(READ, "IMG_8664.md")

    assert [(pair.left, pair.right) for pair in read] == [
        ("Apple", "Apfel"),
        ("Book", "Buch"),
        ("Cat", "Katze"),
        ("Water", "Wasser"),
    ]
    assert read[0].sides == ("", "")


def test_two_or_more_spaces_and_a_tab_are_both_a_gap() -> None:
    read = pairs_in("Apple    Apfel\nBook\tBuch", "shot.md")

    assert [(pair.left, pair.right) for pair in read] == [
        ("Apple", "Apfel"),
        ("Book", "Buch"),
    ]


def test_a_word_holding_a_hyphen_is_not_split_at_it() -> None:
    read = pairs_in("e-mail — E-Mail", "shot.md")

    assert [(pair.left, pair.right) for pair in read] == [("e-mail", "E-Mail")]


def test_a_line_with_one_word_is_no_pair() -> None:
    assert pairs_in("Apple\n\nBook — Buch", "shot.md") == (
        Pair(left="Book", right="Buch", sides=("", ""), source="shot.md"),
    )


def test_prose_holds_no_pairs() -> None:
    assert pairs_in("Just some prose about words and nothing else.", "note.md") == ()


def test_a_heading_is_not_a_pair() -> None:
    read = pairs_in("# English — Einheit 3\n\nApple — Apfel\n", "list.md")

    assert [(pair.left, pair.right) for pair in read] == [("Apple", "Apfel")]
