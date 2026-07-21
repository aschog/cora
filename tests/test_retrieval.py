import dataclasses

import pytest

from docchat.chunk import Chunk
from docchat.retrieval import RetrievedChunk


def _chunk(
    text: str = "hello",
    source: str = "notes.txt",
    index: int = 0,
    offset: int = 0,
) -> Chunk:
    return Chunk(text=text, source=source, index=index, offset=offset)


def test_retrieved_chunks_are_equal_by_content() -> None:
    a = RetrievedChunk(chunk=_chunk(), score=0.9)
    b = RetrievedChunk(chunk=_chunk(), score=0.9)

    assert a == b


def test_retrieved_chunks_differ_when_chunk_or_score_differs() -> None:
    base = RetrievedChunk(chunk=_chunk(), score=0.9)

    assert base != RetrievedChunk(chunk=_chunk(text="world"), score=0.9)
    assert base != RetrievedChunk(chunk=_chunk(), score=0.1)


def test_retrieved_chunk_carries_its_chunk_and_score() -> None:
    chunk = _chunk(index=2, offset=5)
    hit = RetrievedChunk(chunk=chunk, score=0.42)

    assert hit.chunk == chunk
    assert hit.score == 0.42


def test_retrieved_chunk_is_immutable() -> None:
    hit = RetrievedChunk(chunk=_chunk(), score=0.9)

    with pytest.raises(dataclasses.FrozenInstanceError):
        hit.score = 0.1  # ty: ignore[invalid-assignment]
