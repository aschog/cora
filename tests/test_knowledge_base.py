from collections.abc import Callable

from docchat.chunk import Chunk
from docchat.ingestion import ingest
from docchat.knowledge_base import KnowledgeBase
from fakes import FakeEmbedder, FakeRetriever


def test_add_file_embeds_and_stores_one_record_per_chunk(
    embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    data = ("lorem ipsum dolor sit amet " * 100).encode()
    kb = KnowledgeBase(embedder=embedder, retriever=retriever)

    added = kb.add_file(data, "doc.txt")

    assert added == len(ingest(data, "doc.txt"))
    assert added >= 2
    assert retriever.sources() == ["doc.txt"]

    stored = retriever.query(embedder.embed(["probe"])[0], k=added + 5)
    assert len(stored) == added
    assert all(hit.chunk.source == "doc.txt" for hit in stored)


def test_search_returns_the_relevant_chunk_first(
    embedder: FakeEmbedder, retriever: FakeRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    chunks = [
        make_chunk("alpha", index=0, offset=0),
        make_chunk("beta", index=1, offset=6),
        make_chunk("gamma", index=2, offset=12),
    ]
    retriever.add(chunks, embedder.embed([c.text for c in chunks]), file_hash="h")
    kb = KnowledgeBase(embedder=embedder, retriever=retriever)

    hits = kb.search("beta", k=1)

    assert len(hits) == 1
    assert hits[0].chunk == chunks[1]
    assert hits[0].chunk.source == "doc.txt"
