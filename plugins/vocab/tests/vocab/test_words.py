from cora.plugins.vocab.words import Pair, pairs_in

LIST = """# English — Einheit 3

| Deutsch | English |
| --- | --- |
| Hilfe | help |
| Haus | house |
"""


def test_the_pairs_are_read_out_of_a_list_with_its_language() -> None:
    assert pairs_in(LIST) == (
        Pair(german="Hilfe", learning="help", language="English"),
        Pair(german="Haus", learning="house", language="English"),
    )


def test_a_row_missing_a_side_is_not_a_pair() -> None:
    half = LIST + "| Buch |  |\n"

    assert len(pairs_in(half)) == 2


def test_a_document_that_is_not_a_list_holds_no_pairs() -> None:
    assert pairs_in("Just some prose about words.") == ()


def test_a_list_with_no_heading_still_gives_its_pairs() -> None:
    """The heading names the language, and a list without one is still a list — the
    reader's own file, written by hand or read out of a photo."""
    headless = "| Deutsch | English |\n| --- | --- |\n| Hilfe | help |\n"

    assert pairs_in(headless) == (Pair(german="Hilfe", learning="help", language=""),)
