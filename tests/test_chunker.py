from docchat.chunker import chunk_text


def test_empty_text_yields_no_chunks() -> None:
    assert chunk_text("", source="notes.txt") == []


def test_whitespace_only_text_yields_no_chunks() -> None:
    assert chunk_text("   \n\t  ", source="notes.txt") == []
