from hashlib import sha256

from cora.domain.chunk import Chunk
from cora.engine.ingestion import ingest
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.scoping import running_in
from cora.ports.host import DEFAULT_SCOPE
from fakes import (
    TEXT_LOADERS,
    FakeDocuments,
    FakeEmbedder,
    FakeRetriever,
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


def test_add_file_keeps_the_cleaned_text_of_the_upload(kb: KnowledgeBase) -> None:
    kb.add_file(b"# Protein\n\n\n\nAim for 1.6 g per kg.", "protein.md")

    [hit] = kb.search("protein", k=1)
    kept = kb.text(DEFAULT_SCOPE, hit.chunk.upload)
    assert kept is not None
    assert "Aim for 1.6 g per kg." in kept


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


def test_a_field_is_read_whole_by_name_and_text_in_upload_order(
    kb: KnowledgeBase,
) -> None:
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    kb.add_file(b"Rest a week between blocks.", "rest.md", scope=FITNESS)

    with running_in(frozenset({FITNESS})):
        held = kb.all()

    assert [(each.name, each.text) for each in held] == [
        ("plan.md", PLAN.decode()),
        ("rest.md", "Rest a week between blocks."),
    ]


def test_two_uploads_of_one_name_are_two_documents(kb: KnowledgeBase) -> None:
    """The bytes name an upload, so a day saved twice is two documents under one name —
    the store keeps them apart, and so does the reading."""
    kb.add_file(b"# Deadlift 14 kg\n3 sets of 10", "2026-09-18.md", scope=FITNESS)
    kb.add_file(b"# Swing 14 kg\n2 sets of 10", "2026-09-18.md", scope=FITNESS)

    with running_in(frozenset({FITNESS})):
        held = kb.all()

    assert [(each.name, each.text) for each in held] == [
        ("2026-09-18.md", "# Deadlift 14 kg\n3 sets of 10"),
        ("2026-09-18.md", "# Swing 14 kg\n2 sets of 10"),
    ]


def test_a_name_is_read_back_with_every_upload_oldest_first(kb: KnowledgeBase) -> None:
    kb.add_file(b"# Deadlift 14 kg\n3 sets of 10", "2026-09-18.md", scope=FITNESS)
    kb.add_file(b"# Swing 14 kg\n2 sets of 10", "2026-09-18.md", scope=FITNESS)

    assert [each.text for each in kb.read(FITNESS, "2026-09-18.md")] == [
        "# Deadlift 14 kg\n3 sets of 10",
        "# Swing 14 kg\n2 sets of 10",
    ]
    assert kb.read(FITNESS, "never.md") == []


def test_a_document_whose_file_is_gone_is_left_out(
    kb: KnowledgeBase, retriever: FakeRetriever, documents: FakeDocuments
) -> None:
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    kb.add_file(b"Rest a week between blocks.", "rest.md", scope=FITNESS)
    [gone] = retriever.uploads(FITNESS, "plan.md")
    documents.forget(FITNESS, gone)

    with running_in(frozenset({FITNESS})):
        held = kb.all()

    assert [each.name for each in held] == ["rest.md"]


def test_another_fields_document_is_not_listed(kb: KnowledgeBase) -> None:
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    kb.add_file(KYOTO, "kyoto.md", scope=TRAVEL)

    with running_in(frozenset({TRAVEL})):
        held = kb.all()

    assert [(each.name, each.scope) for each in held] == [("kyoto.md", TRAVEL)]


def test_a_turn_in_two_fields_is_handed_both_each_saying_which(
    kb: KnowledgeBase,
) -> None:
    kb.add_file(PLAN, "plan.md", scope=FITNESS)
    kb.add_file(KYOTO, "kyoto.md", scope=TRAVEL)

    with running_in(frozenset({FITNESS, TRAVEL})):
        held = kb.all()

    assert [(each.name, each.scope) for each in held] == [
        ("plan.md", FITNESS),
        ("kyoto.md", TRAVEL),
    ]


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
