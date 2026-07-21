from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

from docchat.chunk import Chunk
from fakes import FakeEmbedder

if TYPE_CHECKING:
    from docchat.chroma_retriever import ChromaRetriever

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
