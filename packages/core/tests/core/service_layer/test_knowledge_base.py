from collections.abc import Callable
from dataclasses import dataclass, field

import pytest

from cora.core.service_layer.ingestion import ingest
from cora.core.service_layer.knowledge_base import KnowledgeBase
from cora.domain.chunk import Chunk
from cora.domain.errors import EmptyDocumentError, UnsupportedFileTypeError
from cora.domain.metadata_filter import MetadataFilter
from fakes import TEXT_LOADERS, FakeEmbedder, FakeRetriever


def test_add_file_embeds_and_stores_one_record_per_chunk(
    kb: KnowledgeBase, embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    data = ("lorem ipsum dolor sit amet " * 100).encode()

    added = kb.add_file(data, "doc.txt")

    assert added == len(ingest(data, "doc.txt", TEXT_LOADERS))
    assert added >= 2
    assert retriever.sources() == ["doc.txt"]

    stored = retriever.query(embedder.embed(["probe"])[0], k=added + 5)
    assert len(stored) == added
    assert all(hit.chunk.source == "doc.txt" for hit in stored)


def test_search_returns_the_relevant_chunk_first(
    kb: KnowledgeBase,
    embedder: FakeEmbedder,
    retriever: FakeRetriever,
    make_chunk: Callable[..., Chunk],
) -> None:
    chunks = [
        make_chunk("alpha", index=0, offset=0),
        make_chunk("beta", index=1, offset=6),
        make_chunk("gamma", index=2, offset=12),
    ]
    retriever.add(chunks, embedder.embed([c.text for c in chunks]), file_hash="h")

    hits = kb.search("beta", k=1)

    assert len(hits) == 1
    assert hits[0].chunk == chunks[1]
    assert hits[0].chunk.source == "doc.txt"


def test_search_narrows_to_the_filtered_source(
    kb: KnowledgeBase,
    embedder: FakeEmbedder,
    retriever: FakeRetriever,
    make_chunk: Callable[..., Chunk],
) -> None:
    chunks = [
        make_chunk("alpha", source="one.txt", index=0),
        make_chunk("beta", source="two.txt", index=0),
    ]
    retriever.add(chunks, embedder.embed([c.text for c in chunks]), file_hash="h")

    hits = kb.search(
        "alpha", k=10, metadata_filter=MetadataFilter(field="source", value="two.txt")
    )

    assert [hit.chunk.source for hit in hits] == ["two.txt"]


def test_search_on_empty_knowledge_base_returns_no_hits(kb: KnowledgeBase) -> None:
    assert kb.search("anything", k=5) == []


def test_list_sources_returns_each_source_once(kb: KnowledgeBase) -> None:
    kb.add_file(("first document " * 100).encode(), "one.txt")
    kb.add_file(("second document " * 100).encode(), "two.md")

    assert kb.list_sources() == ["one.txt", "two.md"]


class _CountingEmbedder:
    def __init__(self) -> None:
        self._inner = FakeEmbedder()
        self.calls = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return self._inner.embed(texts)


def test_re_adding_identical_bytes_is_a_no_op(retriever: FakeRetriever) -> None:
    data = ("same content " * 100).encode()
    embedder = _CountingEmbedder()
    kb = KnowledgeBase(embedder=embedder, retriever=retriever, loaders=TEXT_LOADERS)

    first = kb.add_file(data, "doc.txt")
    second = kb.add_file(data, "doc.txt")

    assert first >= 1
    assert second == 0
    assert embedder.calls == 1
    assert kb.list_sources() == ["doc.txt"]

    stored = retriever.query(FakeEmbedder().embed(["probe"])[0], k=first + 5)
    assert len(stored) == first


@dataclass
class FakeKeywordIndex:
    added: list[Chunk] = field(default_factory=list)

    def add(self, chunks: list[Chunk]) -> None:
        self.added.extend(chunks)


def test_add_file_fans_out_the_same_chunks_to_the_keyword_index(
    embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    keyword = FakeKeywordIndex()
    kb = KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=TEXT_LOADERS,
        keyword_index=keyword,
    )
    data = ("protein supports muscle " * 100).encode()

    kb.add_file(data, "doc.txt")

    assert keyword.added == ingest(data, "doc.txt", TEXT_LOADERS)


def test_duplicate_reupload_leaves_the_keyword_index_untouched(
    embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    keyword = FakeKeywordIndex()
    kb = KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=TEXT_LOADERS,
        keyword_index=keyword,
    )
    data = ("protein supports muscle " * 100).encode()

    kb.add_file(data, "doc.txt")
    after_first = list(keyword.added)
    second = kb.add_file(data, "doc.txt")

    assert second == 0
    assert keyword.added == after_first


def test_add_file_propagates_ingestion_errors_unchanged(kb: KnowledgeBase) -> None:
    with pytest.raises(UnsupportedFileTypeError):
        kb.add_file(b"data", "sheet.xlsx")

    with pytest.raises(EmptyDocumentError):
        kb.add_file(b"   ", "blank.txt")
