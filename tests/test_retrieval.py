import dataclasses

import pytest

from docchat.retrieval import RetrievedChunk


def test_retrieved_chunks_are_equal_by_content() -> None:
    a = RetrievedChunk(text="hello", source="notes.txt", index=0, offset=0, score=0.9)
    b = RetrievedChunk(text="hello", source="notes.txt", index=0, offset=0, score=0.9)

    assert a == b


def test_retrieved_chunks_differ_when_any_field_differs() -> None:
    base = RetrievedChunk(
        text="hello", source="notes.txt", index=0, offset=0, score=0.9
    )

    assert base != RetrievedChunk(
        text="world", source="notes.txt", index=0, offset=0, score=0.9
    )
    assert base != RetrievedChunk(
        text="hello", source="other.txt", index=0, offset=0, score=0.9
    )
    assert base != RetrievedChunk(
        text="hello", source="notes.txt", index=1, offset=0, score=0.9
    )
    assert base != RetrievedChunk(
        text="hello", source="notes.txt", index=0, offset=5, score=0.9
    )
    assert base != RetrievedChunk(
        text="hello", source="notes.txt", index=0, offset=0, score=0.1
    )


def test_retrieved_chunk_carries_provenance_and_score() -> None:
    chunk = RetrievedChunk(
        text="hello", source="notes.txt", index=2, offset=5, score=0.42
    )

    assert (chunk.text, chunk.source, chunk.index, chunk.offset, chunk.score) == (
        "hello",
        "notes.txt",
        2,
        5,
        0.42,
    )


def test_retrieved_chunk_is_immutable() -> None:
    chunk = RetrievedChunk(
        text="hello", source="notes.txt", index=0, offset=0, score=0.9
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        chunk.score = 0.1  # ty: ignore[invalid-assignment]
