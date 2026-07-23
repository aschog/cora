from core.cleaning import clean_text


def test_crlf_becomes_lf() -> None:
    assert clean_text("a\r\nb\r\nc") == "a\nb\nc"


def test_lone_cr_becomes_lf() -> None:
    assert clean_text("a\rb") == "a\nb"


def test_surrounding_whitespace_is_trimmed() -> None:
    assert clean_text("  \n hello \n  ") == "hello"


def test_runs_of_blank_lines_collapse_to_one_paragraph_break() -> None:
    assert clean_text("a\n\n\n\nb") == "a\n\nb"


def test_ordinary_paragraph_break_is_preserved() -> None:
    assert clean_text("a\n\nb") == "a\n\nb"
