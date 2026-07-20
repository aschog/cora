from docchat.chunk import Chunk
from docchat.chunker import chunk_text


def test_empty_text_yields_no_chunks() -> None:
    assert chunk_text("", source="notes.txt") == []


def test_text_shorter_than_chunk_size_yields_one_chunk() -> None:
    chunks = chunk_text("A short note.", source="notes.txt", chunk_size=1000)

    assert chunks == [
        Chunk(text="A short note.", source="notes.txt", index=0, offset=0)
    ]


def test_whitespace_only_text_yields_no_chunks() -> None:
    assert chunk_text("   \n\t  ", source="notes.txt") == []
