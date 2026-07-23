import itertools

import pytest

from core.chunk import Chunk
from core.chunker import chunk_text


def test_empty_text_yields_no_chunks() -> None:
    assert chunk_text("", source="notes.txt") == []


def test_text_shorter_than_chunk_size_yields_one_chunk() -> None:
    chunks = chunk_text("A short note.", source="notes.txt", chunk_size=1000)

    assert chunks == [
        Chunk(text="A short note.", source="notes.txt", index=0, offset=0)
    ]


def test_whitespace_only_text_yields_no_chunks() -> None:
    assert chunk_text("   \n\t  ", source="notes.txt") == []


def test_splits_at_paragraph_break_near_size_limit() -> None:
    para1 = "A" * 40
    para2 = "B" * 40
    text = f"{para1}\n\n{para2}"

    chunks = chunk_text(text, source="notes.txt", chunk_size=50, overlap=0)

    assert [chunk.text for chunk in chunks] == [para1, para2]


def test_splits_at_line_breaks_when_no_paragraph_breaks() -> None:
    line1 = "A" * 40
    line2 = "B" * 40
    text = f"{line1}\n{line2}"

    chunks = chunk_text(text, source="notes.txt", chunk_size=50, overlap=0)

    assert [chunk.text for chunk in chunks] == [line1, line2]


def test_splits_at_word_boundaries_when_no_line_breaks() -> None:
    word1 = "A" * 40
    word2 = "B" * 40
    text = f"{word1} {word2}"

    chunks = chunk_text(text, source="notes.txt", chunk_size=50, overlap=0)

    assert [chunk.text for chunk in chunks] == [word1, word2]


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


def test_offsets_stay_valid_when_source_has_separator_runs() -> None:
    text = "  ".join(f"word{n}" for n in range(400))

    chunks = chunk_text(text, source="notes.txt", chunk_size=100, overlap=20)

    assert all(chunk.text for chunk in chunks)
    offsets = [chunk.offset for chunk in chunks]
    assert offsets == sorted(offsets)
    assert all(offset >= 0 for offset in offsets)
    for chunk in chunks:
        assert text[chunk.offset : chunk.offset + len(chunk.text)] == chunk.text


def test_chunk_indices_are_consecutive_and_offsets_locate_text() -> None:
    text = "\n\n".join(f"Paragraph number {n} with some words." for n in range(30))

    chunks = chunk_text(text, source="notes.txt", chunk_size=80, overlap=15)

    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
    for chunk in chunks:
        assert text[chunk.offset : chunk.offset + len(chunk.text)] == chunk.text


def test_long_text_splits_into_multiple_chunks_within_budget() -> None:
    text = ". ".join(f"sentence number {n}" for n in range(200))

    chunks = chunk_text(text, source="notes.txt", chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 100 for chunk in chunks)


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_non_positive_chunk_size_is_rejected(chunk_size: int) -> None:
    with pytest.raises(ValueError):
        chunk_text("text", source="notes.txt", chunk_size=chunk_size)


@pytest.mark.parametrize("overlap", [10, 11])
def test_overlap_not_smaller_than_chunk_size_is_rejected(overlap: int) -> None:
    with pytest.raises(ValueError):
        chunk_text("text", source="notes.txt", chunk_size=10, overlap=overlap)


def test_negative_overlap_is_rejected() -> None:
    with pytest.raises(ValueError):
        chunk_text("text", source="notes.txt", chunk_size=10, overlap=-1)
