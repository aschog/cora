from collections.abc import Callable
from dataclasses import replace

import pytest

from cora.domain.chunk import Chunk
from cora.domain.errors import (
    DocumentStoreError,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)
from cora.engine.ingestion import ingest
from cora.engine.knowledge_base import KnowledgeBase
from fakes import (
    TEXT_LOADERS,
    FailingDocuments,
    FakeDocuments,
    FakeEmbedder,
    FakeRetriever,
    KeepsNothingDocuments,
)


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
    assert hits[0].chunk == replace(chunks[1], upload="h")
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


def test_add_file_keeps_the_cleaned_text_of_the_upload(kb: KnowledgeBase) -> None:
    kb.add_file(b"# Protein\n\n\n\nAim for 1.6 g per kg.", "protein.md")

    [hit] = kb.search("protein", k=1)
    kept = kb.text(hit.chunk.upload)
    assert kept is not None
    assert "Aim for 1.6 g per kg." in kept


def test_every_chunks_offset_points_at_that_chunks_text(kb: KnowledgeBase) -> None:
    """The invariant the citation pane rests on: a highlight is drawn by slicing the
    kept text with a chunk's offsets, so slicing has to give the chunk back — over a
    document long enough to chunk with overlap."""
    data = "\n\n".join(f"Paragraph {n} with several words in it." for n in range(80))

    added = kb.add_file(data.encode(), "long.md")

    assert added > 1
    hits = kb.search("paragraph", k=added)
    assert len(hits) == added
    text = kb.text(hits[0].chunk.upload)
    assert text is not None
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


def test_the_text_of_an_unknown_document_is_nothing(kb: KnowledgeBase) -> None:
    assert kb.text("never-uploaded.md") is None


class _KeepFails(FakeDocuments):
    def keep(self, upload: str, text: str) -> None:
        raise DocumentStoreError


def test_a_document_whose_text_cannot_be_kept_is_never_searchable(
    embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    """A passage in the index is a citation waiting to be shown, and a citation whose
    text was never kept opens onto nothing. The store that keeps the text is written
    first, so a failure there costs the upload rather than leaving it half done — and
    the user is told, instead of being told it worked on the retry."""
    kb = KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=TEXT_LOADERS,
        documents=_KeepFails(),
    )

    with pytest.raises(DocumentStoreError):
        kb.add_file(b"Aim for 1.6 g of protein per kg.", "protein.md")

    assert retriever.sources() == []
    assert kb.search("protein", k=5) == []


V1 = b"Version one says: aim for 1.6 g of protein per kg of bodyweight every day."
V2 = b"PREFACE ADDED LATER. Version two says: aim for 2.0 g of protein per kg."


def test_a_passage_reads_back_the_text_it_was_cut_from(kb: KnowledgeBase) -> None:
    """The promise a citation makes. A file edited and uploaded again under the same
    name is different content: the passage found in the first upload still slices the
    first upload's text, because a span is only meaningful against the text it was
    measured in."""
    kb.add_file(V1, "report.md")
    [first] = kb.search("protein", k=1)

    kb.add_file(V2, "report.md")

    text = kb.text(first.chunk.upload)
    assert text is not None
    chunk = first.chunk
    assert text[chunk.offset : chunk.offset + len(chunk.text)] == chunk.text
    assert "Version one" in text


def test_uploading_a_file_again_repairs_text_the_index_never_had(
    embedder: FakeEmbedder, retriever: FakeRetriever, documents: FakeDocuments
) -> None:
    """An index written before its documents were kept answers with citations that open
    onto nothing, and `contains` would keep it that way for good. Uploading the same
    file again is the repair: no second copy in the index, and the passages become
    readable."""
    data = b"Aim for 1.6 g of protein per kg."
    indexed_only = KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=TEXT_LOADERS,
        documents=KeepsNothingDocuments(),
    )
    indexed_only.add_file(data, "protein.md")
    [before] = retriever.query(embedder.embed(["protein"])[0], k=1)
    assert documents.read(before.chunk.upload) is None

    kb = KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=TEXT_LOADERS,
        documents=documents,
    )
    added = kb.add_file(data, "protein.md")

    assert added == 0, "the index already has it, so nothing is indexed twice"
    assert kb.text(before.chunk.upload) == "Aim for 1.6 g of protein per kg."
    assert len(retriever.query(embedder.embed(["protein"])[0], k=5)) == 1


def test_a_repair_that_cannot_read_the_store_says_so_and_writes_nothing(
    embedder: FakeEmbedder, retriever: FakeRetriever
) -> None:
    """Uploading a file the index already holds now asks the document store a question,
    which is a branch that used to be incapable of failing. It fails like every other
    adapter: the user is told, and nothing is half written."""
    data = b"Aim for 1.6 g of protein per kg."
    documents = FailingDocuments()
    kb = KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=TEXT_LOADERS,
        documents=documents,
    )
    kb.add_file(data, "protein.md")
    kept = documents.writes

    with pytest.raises(DocumentStoreError):
        kb.add_file(data, "protein.md")

    assert documents.writes == kept
