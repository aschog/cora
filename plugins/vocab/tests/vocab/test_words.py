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
    """The reading drops a side now and then. The line goes, the list stays — as long
    as the rest of the document still reads as a list."""
    read = pairs_in("Apple\nBook — Buch\nCat — Katze\nDog — Hund\n", "shot.md")

    assert [(pair.left, pair.right) for pair in read] == [
        ("Book", "Buch"),
        ("Cat", "Katze"),
        ("Dog", "Hund"),
    ]


def test_prose_holds_no_pairs() -> None:
    assert pairs_in("Just some prose about words and nothing else.", "note.md") == ()


def test_a_heading_is_not_a_pair() -> None:
    read = pairs_in("# English — Einheit 3\n\nApple — Apfel\n", "list.md")

    assert [(pair.left, pair.right) for pair in read] == [("Apple", "Apfel")]


PROSE = """Der Kurs beginnt am Montag — das habe ich vergessen.
Bring your own laptop  and a notebook.
Wir treffen uns um acht — bitte nicht zu spät kommen.
"""


def test_prose_split_by_a_dash_is_not_a_list_of_pairs() -> None:
    """A note left in the field is a note: a sentence either side of a dash is not a
    word and its translation, and a drill that took it for one would put paragraphs to
    the reader to translate."""
    assert pairs_in(PROSE, "notes.md") == ()


def test_a_line_whose_sides_are_phrases_is_no_pair() -> None:
    read = pairs_in(
        "Apple — Apfel\nBring your own laptop  and a notebook.\nBook — Buch\n",
        "shot.md",
    )

    assert [(pair.left, pair.right) for pair in read] == [
        ("Apple", "Apfel"),
        ("Book", "Buch"),
    ]


def test_a_document_that_is_mostly_prose_holds_no_pairs() -> None:
    """One line that looks like a pair does not make a page of prose a list."""
    mostly = PROSE + "Apple — Apfel\n"

    assert pairs_in(mostly, "notes.md") == ()


def test_a_short_phrase_is_still_a_word() -> None:
    """Vocabulary is not always one word: "to look after" is what a list of verbs
    holds, and the cap is on prose rather than on phrases."""
    read = pairs_in("to look after — sich kümmern um\nhouse — Haus\n", "verbs.md")

    assert [(pair.left, pair.right) for pair in read] == [
        ("to look after", "sich kümmern um"),
        ("house", "Haus"),
    ]
