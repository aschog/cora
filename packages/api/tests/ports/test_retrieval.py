from collections.abc import Callable

from cora.domain.chunk import Chunk
from cora.ports.retrieval import RetrievedChunk


def test_retrieved_chunks_are_equal_by_content(
    make_chunk: Callable[..., Chunk],
) -> None:
    a = RetrievedChunk(chunk=make_chunk(), score=0.9)
    b = RetrievedChunk(chunk=make_chunk(), score=0.9)

    assert a == b


def test_retrieved_chunks_differ_when_chunk_or_score_differs(
    make_chunk: Callable[..., Chunk],
) -> None:
    base = RetrievedChunk(chunk=make_chunk(), score=0.9)

    assert base != RetrievedChunk(chunk=make_chunk(text="world"), score=0.9)
    assert base != RetrievedChunk(chunk=make_chunk(), score=0.1)


def test_retrieved_chunk_carries_its_chunk_and_score(
    make_chunk: Callable[..., Chunk],
) -> None:
    chunk = make_chunk(index=2, offset=5)
    hit = RetrievedChunk(chunk=chunk, score=0.42)

    assert hit.chunk == chunk
    assert hit.score == 0.42
