from collections.abc import Callable
from dataclasses import replace
from hashlib import sha256

import pytest

from cora.domain.chunk import Chunk
from cora.domain.errors import (
    DocumentStoreError,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)
from cora.engine.ingestion import ingest
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.scoping import running_in
from cora.ports.host import DEFAULT_SCOPE
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
    assert retriever.sources(DEFAULT_SCOPE) == ["doc.txt"]

    stored = retriever.query(DEFAULT_SCOPE, embedder.embed(["probe"])[0], k=added + 5)
    assert len(stored) == added
    assert all(hit.chunk.source == "doc.txt" for hit in stored)


def test_search_returns_the_relevant_chunk_first(
    kb: KnowledgeBase,
    embedder: FakeEmbedder,
    retriever: FakeRetriever,
    documents: FakeDocuments,
    make_chunk: Callable[..., Chunk],
) -> None:
    """The text is kept beside the index because a hit's words are sliced out of it."""
    documents.keep(DEFAULT_SCOPE, "h", "doc.txt", "alpha beta gamma")
    chunks = [
        make_chunk("alpha", index=0, offset=0),
        make_chunk("beta", index=1, offset=6),
        make_chunk("gamma", index=2, offset=12),
    ]
    retriever.add(
        DEFAULT_SCOPE,
        chunks,
        embedder.embed([c.text for c in chunks]),
        file_hash="h",
    )

    hits = kb.search("beta", k=1)

    assert len(hits) == 1
    assert hits[0].chunk == replace(chunks[1], upload="h", scope=DEFAULT_SCOPE)
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

    stored = retriever.query(
        DEFAULT_SCOPE, FakeEmbedder().embed(["probe"])[0], k=first + 5
    )
    assert len(stored) == first


def test_add_file_propagates_ingestion_errors_unchanged(kb: KnowledgeBase) -> None:
    with pytest.raises(UnsupportedFileTypeError):
        kb.add_file(b"data", "sheet.xlsx")

    with pytest.raises(EmptyDocumentError):
        kb.add_file(b"   ", "blank.txt")


def test_add_file_keeps_the_cleaned_text_of_the_upload(kb: KnowledgeBase) -> None:
    kb.add_file(b"# Protein\n\n\n\nAim for 1.6 g per kg.", "protein.md")

    [hit] = kb.search("protein", k=1)
    kept = kb.text(DEFAULT_SCOPE, hit.chunk.upload)
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
    text = kb.text(DEFAULT_SCOPE, hits[0].chunk.upload)
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
    assert kb.text(DEFAULT_SCOPE, "never-uploaded.md") is None


class _KeepFails(FakeDocuments):
    def keep(self, scope: str, upload: str, filename: str, text: str) -> None:
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

    assert retriever.sources(DEFAULT_SCOPE) == []
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

    text = kb.text(DEFAULT_SCOPE, first.chunk.upload)
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
    [before] = retriever.query(DEFAULT_SCOPE, embedder.embed(["protein"])[0], k=1)
    assert documents.read(DEFAULT_SCOPE, before.chunk.upload) is None

    kb = KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=TEXT_LOADERS,
        documents=documents,
    )
    added = kb.add_file(data, "protein.md")

    assert added == 0, "the index already has it, so nothing is indexed twice"
    assert (
        kb.text(DEFAULT_SCOPE, before.chunk.upload)
        == "Aim for 1.6 g of protein per kg."
    )
    assert len(retriever.query(DEFAULT_SCOPE, embedder.embed(["protein"])[0], k=5)) == 1


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


FITNESS, TRAVEL = "fitness", "travel"
PLAN = b"The block holds intensity and drops volume in the fourth week."
KYOTO = b"The sleeper to Kyoto sells out a month before the maples turn."


def test_a_field_retrieves_its_own_documents_and_no_others(kb: KnowledgeBase) -> None:
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    kb.add_file(KYOTO, "kyoto.md", scope=TRAVEL)

    with running_in(frozenset({TRAVEL})):
        hits = kb.search("what do my notes say", k=5)

    assert [hit.chunk.source for hit in hits] == ["kyoto.md"]
    assert all(hit.chunk.scope == TRAVEL for hit in hits)


def test_a_field_with_nothing_in_it_finds_nothing(kb: KnowledgeBase) -> None:
    kb.add_file(PLAN, "plan.md", scope=FITNESS)

    with running_in(frozenset({TRAVEL})):
        assert kb.search("intensity", k=5) == []


def test_the_sources_of_a_field_are_its_own(kb: KnowledgeBase) -> None:
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    kb.add_file(KYOTO, "kyoto.md", scope=TRAVEL)

    assert kb.list_sources(FITNESS) == ["plan.md"]
    assert kb.list_sources(TRAVEL) == ["kyoto.md"]


def test_the_same_bytes_are_indexed_in_every_field_they_are_added_to(
    kb: KnowledgeBase,
) -> None:
    """`contains` is asked within a field, so a document already in one is still new to
    the next — a field is meant to be self-contained."""
    assert kb.add_file(PLAN, "plan.md", scope=FITNESS) >= 1
    assert kb.add_file(PLAN, "plan.md", scope=TRAVEL) >= 1

    assert kb.list_sources(TRAVEL) == ["plan.md"]


def test_a_search_with_no_field_bound_reads_the_default_one(kb: KnowledgeBase) -> None:
    kb.add_file(PLAN, "plan.md")

    assert [hit.chunk.source for hit in kb.search("intensity", k=5)] == ["plan.md"]


def test_a_passage_carries_the_text_at_its_span_read_from_the_file(
    kb: KnowledgeBase, documents: FakeDocuments
) -> None:
    """The index keeps the span and the file keeps the words, so what a search hands
    back is sliced out of the file — which is why editing the file changes what a
    passage says, and why the index alone could not have answered."""
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    documents.keep(FITNESS, sha256(PLAN).hexdigest(), "plan.md", "REWRITTEN.")

    with running_in(frozenset({FITNESS})):
        [hit] = kb.search("intensity", k=1)

    assert hit.chunk.text == "REWRITTEN."


def test_a_passage_whose_file_is_gone_is_left_out(
    kb: KnowledgeBase, documents: FakeDocuments
) -> None:
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    documents.emptied(FITNESS)

    with running_in(frozenset({FITNESS})):
        assert kb.search("intensity", k=5) == []


def test_a_missing_file_costs_its_own_place_and_not_the_one_below_it(
    kb: KnowledgeBase, documents: FakeDocuments
) -> None:
    """A turn running in two fields merges what each returned, so cutting to `k` before
    the unreadable passages are dropped spends a place on a passage nobody gets."""
    kb.add_file(KYOTO, "kyoto.md", scope=TRAVEL)
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    documents.emptied(TRAVEL)

    with running_in(frozenset({FITNESS, TRAVEL})):
        [hit] = kb.search(KYOTO.decode(), k=1)

    assert hit.chunk.source == "plan.md"


class _RecordingRetriever(FakeRetriever):
    """What the index was handed, as the port promises it: the span, and no words."""

    def __init__(self) -> None:
        super().__init__()
        self.given: list[Chunk] = []

    def add(
        self,
        scope: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
        file_hash: str,
    ) -> None:
        self.given.extend(chunks)
        super().add(scope, chunks, vectors, file_hash)


def test_the_index_is_handed_the_span_and_none_of_the_words(
    documents: FakeDocuments, embedder: FakeEmbedder
) -> None:
    """The file is where the text is kept, so handing it to the index as well would be
    the second copy the story exists to remove."""
    retriever = _RecordingRetriever()
    kb = KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=TEXT_LOADERS,
        documents=documents,
    )

    kb.add_file(PLAN, "plan.md", scope=FITNESS)

    assert retriever.given
    assert all(chunk.text == "" for chunk in retriever.given)
    assert sum(chunk.length for chunk in retriever.given) >= len(PLAN.decode())


def test_a_passage_whose_file_was_cut_short_is_left_out(
    kb: KnowledgeBase, documents: FakeDocuments
) -> None:
    """A file is cora's to write but a person's to read, and one edited down to less
    than a passage's span leaves that passage nothing to say. It is left out for the
    same reason a missing one is: an empty passage would be cited as though it spoke."""
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    documents.keep(FITNESS, sha256(PLAN).hexdigest(), "plan.md", "")

    with running_in(frozenset({FITNESS})):
        assert kb.search("intensity", k=5) == []


def test_forgetting_a_document_drops_its_passages_and_its_file(
    kb: KnowledgeBase, documents: FakeDocuments, retriever: FakeRetriever
) -> None:
    """One call over both halves: a document gone from one of them is still half there
    — listed and unopenable, or a file nothing can reach."""
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    kb.add_file(KYOTO, "kyoto.md", scope=FITNESS)

    kb.forget(FITNESS, "plan.md")

    assert kb.list_sources(FITNESS) == ["kyoto.md"]
    assert documents.read(FITNESS, sha256(PLAN).hexdigest()) is None
    with running_in(frozenset({FITNESS})):
        assert [hit.chunk.source for hit in kb.search("intensity", k=5)] == ["kyoto.md"]


def test_forgetting_a_name_uploaded_twice_takes_both_uploads(
    kb: KnowledgeBase, documents: FakeDocuments
) -> None:
    """The rail lists a name and the stores keep uploads, so one row may be two
    documents: what the reader deleted is the row."""
    edited = PLAN + b" And it deloads in the fifth."
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    kb.add_file(edited, "plan.md", scope=FITNESS)

    kb.forget(FITNESS, "plan.md")

    assert kb.list_sources(FITNESS) == []
    assert documents.read(FITNESS, sha256(PLAN).hexdigest()) is None
    assert documents.read(FITNESS, sha256(edited).hexdigest()) is None


def test_another_field_keeps_its_own_copy_of_a_deleted_document(
    kb: KnowledgeBase, documents: FakeDocuments
) -> None:
    """A field owns its documents, so the same file in two of them is two documents."""
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    kb.add_file(PLAN, "plan.md", scope=TRAVEL)

    kb.forget(FITNESS, "plan.md")

    assert kb.list_sources(TRAVEL) == ["plan.md"]
    assert documents.read(TRAVEL, sha256(PLAN).hexdigest()) == PLAN.decode()


def test_the_index_is_dropped_before_the_file(kb: KnowledgeBase) -> None:
    """Ingestion keeps the text and then indexes it, so a passage is never citable
    before it is openable. Deleting runs that backwards: a failure halfway leaves a
    file nothing can reach, rather than a document listed with its text gone."""
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    broken = KnowledgeBase(
        embedder=kb.embedder,
        retriever=kb.retriever,
        loaders=kb.loaders,
        documents=FailingDocuments(),
    )

    with pytest.raises(DocumentStoreError):
        broken.forget(FITNESS, "plan.md")

    assert broken.list_sources(FITNESS) == [], "the index went first"


def test_a_deleted_document_is_indexed_again_when_it_is_uploaded_again(
    kb: KnowledgeBase, documents: FakeDocuments
) -> None:
    """The way back from a mistake: the bytes name the upload, and nothing that would
    make them look already-indexed is left behind."""
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    kb.forget(FITNESS, "plan.md")

    added = kb.add_file(PLAN, "plan.md", scope=FITNESS)

    assert added > 0
    assert kb.list_sources(FITNESS) == ["plan.md"]
    assert documents.read(FITNESS, sha256(PLAN).hexdigest()) == PLAN.decode()


def test_forgetting_a_name_nothing_was_uploaded_under_is_not_an_error(
    kb: KnowledgeBase,
) -> None:
    kb.forget(FITNESS, "never-uploaded.md")

    assert kb.list_sources(FITNESS) == []
