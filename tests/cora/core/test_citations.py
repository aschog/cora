from cora.core.citations import cited_numbers


def test_cited_numbers_are_distinct_in_order_of_first_appearance() -> None:
    assert cited_numbers("uses [3], then [1], and [3] again") == (3, 1)
    assert cited_numbers("no brackets here") == ()


def test_cited_numbers_ignores_brackets_glued_to_a_word_or_bracket() -> None:
    assert cited_numbers("write list[2] or arr[0][1], then cite [1]") == (1,)


def test_cited_numbers_reads_every_number_in_a_consecutive_run() -> None:
    assert cited_numbers("a balanced diet [3][1][2].") == (3, 1, 2)
    assert cited_numbers("see [10][2].") == (10, 2)
