from cora.adapters.port_logging import MAX_LOGGED_CHARS, truncate


def test_truncate_passes_text_within_the_cap_through_unchanged() -> None:
    text = "short enough to log in full"

    assert truncate(text) == text


def test_truncate_bounds_long_text_and_marks_the_cut() -> None:
    clipped = truncate("x" * (MAX_LOGGED_CHARS * 3))

    assert len(clipped) <= MAX_LOGGED_CHARS
    assert clipped.endswith("…")
