import itertools

import pytest

from cora.engine.chunker import chunk_text


def test_empty_text_yields_no_chunks() -> None:
    assert chunk_text("", source="notes.txt") == []


def test_splits_at_paragraph_break_near_size_limit() -> None:
    para1 = "A" * 40
    para2 = "B" * 40
    text = f"{para1}\n\n{para2}"

    chunks = chunk_text(text, source="notes.txt", chunk_size=50, overlap=0)

    assert [chunk.text for chunk in chunks] == [para1, para2]


def test_unbroken_run_longer_than_chunk_size_is_hard_split() -> None:
    text = "A" * 250

    chunks = chunk_text(text, source="notes.txt", chunk_size=100, overlap=0)

    assert [chunk.text for chunk in chunks] == ["A" * 100, "A" * 100, "A" * 50]
    assert "".join(chunk.text for chunk in chunks) == text


def test_consecutive_chunks_overlap_by_configured_amount() -> None:
    text = "".join(chr(ord("a") + (i % 26)) for i in range(300))
    chunk_size, overlap = 100, 20

    chunks = chunk_text(
        text, source="notes.txt", chunk_size=chunk_size, overlap=overlap
    )

    assert len(chunks) > 1
    assert all(len(chunk.text) <= chunk_size for chunk in chunks)
    for prev, nxt in itertools.pairwise(chunks):
        assert nxt.text[:overlap] == prev.text[-overlap:]


def test_chunk_indices_are_consecutive_and_offsets_locate_text() -> None:
    text = "\n\n".join(f"Paragraph number {n} with some words." for n in range(30))

    chunks = chunk_text(text, source="notes.txt", chunk_size=80, overlap=15)

    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
    for chunk in chunks:
        assert text[chunk.offset : chunk.offset + len(chunk.text)] == chunk.text


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_non_positive_chunk_size_is_rejected(chunk_size: int) -> None:
    with pytest.raises(ValueError):
        chunk_text("text", source="notes.txt", chunk_size=chunk_size)


@pytest.mark.parametrize("overlap", [10, 11])
def test_overlap_not_smaller_than_chunk_size_is_rejected(overlap: int) -> None:
    with pytest.raises(ValueError):
        chunk_text("text", source="notes.txt", chunk_size=10, overlap=overlap)
