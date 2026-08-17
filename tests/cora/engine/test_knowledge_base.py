from collections.abc import Callable

import pytest

from cora.domain.chunk import Chunk
from cora.domain.errors import EmptyDocumentError, UnsupportedFileTypeError
from cora.engine.ingestion import ingest
from cora.engine.knowledge_base import KnowledgeBase
from fakes import TEXT_LOADERS, FakeDocuments, FakeEmbedder, FakeRetriever


def test_add_file_embeds_and_stores_one_record_per_chunk(
    kb: KnowledgeBase, embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    data = ("lorem ipsum dolor sit amet " * 100).encode()

    added = kb.add_file(data, "doc.txt")

    assert added == len(ingest(data, "doc.txt", TEXT_LOADERS).chunks)
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
    kb = KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=TEXT_LOADERS,
        documents=FakeDocuments(),
    )

    first = kb.add_file(data, "doc.txt")
    second = kb.add_file(data, "doc.txt")

    assert first >= 1
    assert second == 0
    assert embedder.calls == 1
    assert kb.list_sources() == ["doc.txt"]

    stored = retriever.query(FakeEmbedder().embed(["probe"])[0], k=first + 5)
    assert len(stored) == first


def test_add_file_propagates_ingestion_errors_unchanged(kb: KnowledgeBase) -> None:
    with pytest.raises(UnsupportedFileTypeError):
        kb.add_file(b"data", "sheet.xlsx")

    with pytest.raises(EmptyDocumentError):
        kb.add_file(b"   ", "blank.txt")


def test_add_file_keeps_the_cleaned_text_under_the_documents_name(
    kb: KnowledgeBase, documents: FakeDocuments
) -> None:
    kb.add_file(b"# Protein\n\n\n\nAim for 1.6 g per kg.", "protein.md")

    kept = documents.read("protein.md")
    assert kept is not None
    assert "Aim for 1.6 g per kg." in kept


def test_every_chunks_offset_points_at_that_chunks_text(kb: KnowledgeBase) -> None:
    """The invariant the citation pane rests on: a highlight is drawn by slicing the
    kept text with a chunk's offsets, so slicing has to give the chunk back — over a
    document long enough to chunk with overlap."""
    data = "\n\n".join(f"Paragraph {n} with several words in it." for n in range(80))

    added = kb.add_file(data.encode(), "long.md")
    text = kb.text("long.md")

    assert added > 1
    assert text is not None
    hits = kb.search("paragraph", k=added)
    assert len(hits) == added
    for hit in hits:
        chunk = hit.chunk
        assert text[chunk.offset : chunk.offset + len(chunk.text)] == chunk.text


def test_a_file_already_indexed_keeps_nothing_further(
    kb: KnowledgeBase, documents: FakeDocuments
) -> None:
    data = ("same content " * 100).encode()

    kb.add_file(data, "doc.txt")
    again = kb.add_file(data, "doc.txt")

    assert again == 0
    assert documents.writes == 1


def test_a_document_that_fails_to_ingest_keeps_nothing(
    kb: KnowledgeBase, documents: FakeDocuments
) -> None:
    with pytest.raises(EmptyDocumentError):
        kb.add_file(b"   ", "blank.txt")

    assert documents.writes == 0
    assert kb.text("blank.txt") is None


def test_the_text_of_an_unknown_document_is_nothing(kb: KnowledgeBase) -> None:
    assert kb.text("never-uploaded.md") is None
