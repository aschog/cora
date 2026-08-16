from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from cora.domain.chunk import Chunk
from cora.domain.errors import RetrievalError
from fakes import FakeEmbedder

if TYPE_CHECKING:
    from cora.adapters.chroma_retriever import ChromaRetriever

pytestmark = pytest.mark.integration


def test_chroma_round_trips_with_our_own_embeddings(
    chroma_retriever: "ChromaRetriever", make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chunks = [
        make_chunk("alpha", index=0),
        make_chunk("beta", index=1),
        make_chunk("gamma", index=2),
    ]
    chroma_retriever.add(
        chunks, embedder.embed([c.text for c in chunks]), file_hash="h"
    )

    [query_vector] = embedder.embed(["beta"])
    hits = chroma_retriever.query(query_vector, k=2)

    assert len(hits) == 2
    assert hits[0].chunk == chunks[1]
    assert hits[0].chunk.source == "doc.txt"
    assert hits[0].score >= hits[1].score


def test_chroma_reads_back_sources_and_contains(
    chroma_retriever: "ChromaRetriever", make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    first = [make_chunk("a", source="one.txt", index=0)]
    second = [
        make_chunk("b", source="two.txt", index=0),
        make_chunk("c", source="two.txt", index=1),
    ]
    chroma_retriever.add(first, embedder.embed(["a"]), file_hash="h1")
    chroma_retriever.add(second, embedder.embed(["b", "c"]), file_hash="h2")

    assert sorted(chroma_retriever.sources()) == ["one.txt", "two.txt"]
    assert chroma_retriever.contains("h1")
    assert not chroma_retriever.contains("h3")


def test_chroma_records_persist_across_a_fresh_client(
    make_chroma: "Callable[[], ChromaRetriever]", make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chunk = make_chunk("persisted", index=0)
    make_chroma().add([chunk], embedder.embed(["persisted"]), file_hash="h")

    reopened = make_chroma()
    hits = reopened.query(embedder.embed(["persisted"])[0], k=1)

    assert len(hits) == 1
    assert hits[0].chunk == chunk


def test_chroma_re_adds_with_same_ids_do_not_duplicate(
    chroma_retriever: "ChromaRetriever", make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chunks = [make_chunk("a", index=0), make_chunk("b", index=1)]
    vectors = embedder.embed([c.text for c in chunks])
    chroma_retriever.add(chunks, vectors, file_hash="h")
    chroma_retriever.add(chunks, vectors, file_hash="h")

    hits = chroma_retriever.query(embedder.embed(["a"])[0], k=10)
    assert len(hits) == 2


def test_chroma_failure_surfaces_as_retrieval_error(
    chroma_retriever: "ChromaRetriever", make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chroma_retriever.add(
        [make_chunk("a", index=0)], embedder.embed(["a"]), file_hash="h"
    )

    with pytest.raises(RetrievalError):
        chroma_retriever.query([0.1, 0.2, 0.3], k=1)


def test_chroma_construction_failure_surfaces_as_retrieval_error(
    tmp_path: Path,
) -> None:
    from cora.adapters.chroma_retriever import ChromaRetriever

    with pytest.raises(RetrievalError):
        ChromaRetriever(path=str(tmp_path), collection="x")
