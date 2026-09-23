from hashlib import sha256

from cora.domain.chunk import Chunk
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.scoping import running_in
from cora.ports.host import DEFAULT_SCOPE
from fakes import FakeDocuments, FakeEmbedder, FakeRetriever

FITNESS, TRAVEL = "fitness", "travel"
PLAN = "The block holds intensity and drops volume in the fourth week."
KYOTO = "The sleeper to Kyoto sells out a month before the maples turn."
LIFTS = ("# Deadlift 14 kg\n3 sets of 10", "# Swing 14 kg\n2 sets of 10")


def _library(retriever: FakeRetriever | None = None) -> KnowledgeBase:
    return KnowledgeBase(
        embedder=FakeEmbedder(),
        retriever=retriever or FakeRetriever(),
        documents=FakeDocuments(),
    )


def _cut(text: str, name: str, size: int = 40) -> list[Chunk]:
    return [
        Chunk(text=text[at : at + size], source=name, index=index, offset=at)
        for index, at in enumerate(range(0, len(text), size))
    ]


def _added(
    kb: KnowledgeBase, text: str, name: str, scope: str = DEFAULT_SCOPE
) -> tuple[str, bool]:
    upload = sha256(text.encode()).hexdigest()
    return upload, kb.add(scope, upload, name, text, _cut(text, name))


def test_add_embeds_and_stores_one_record_per_chunk() -> None:
    retriever = FakeRetriever()
    kb = _library(retriever)
    text = "lorem ipsum dolor sit amet " * 20

    _added(kb, text, "doc.txt")

    assert retriever.sources(DEFAULT_SCOPE) == ["doc.txt"]
    stored = retriever.query(DEFAULT_SCOPE, FakeEmbedder().embed(["probe"])[0], k=99)
    assert len(stored) == len(_cut(text, "doc.txt")) >= 2
    assert all(hit.chunk.source == "doc.txt" for hit in stored)


class _CountingEmbedder(FakeEmbedder):
    calls = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return super().embed(texts)


def test_adding_an_upload_the_field_holds_is_a_no_op() -> None:
    embedder = _CountingEmbedder()
    kb = KnowledgeBase(
        embedder=embedder, retriever=FakeRetriever(), documents=FakeDocuments()
    )

    _, first = _added(kb, PLAN, "plan.md")
    _, second = _added(kb, PLAN, "plan.md")

    assert (first, second) == (True, False)
    assert embedder.calls == 1
    assert kb.list_sources() == ["plan.md"]


def test_a_text_that_went_missing_under_cora_is_put_back_on_the_next_add() -> None:
    kb = _library()
    documents = kb.documents
    assert isinstance(documents, FakeDocuments)
    upload, _ = _added(kb, PLAN, "plan.md")
    documents.forget(DEFAULT_SCOPE, upload)

    _, added = _added(kb, PLAN, "plan.md")

    assert added is False
    assert kb.text(DEFAULT_SCOPE, upload) == PLAN


def test_a_passage_reads_back_the_text_it_was_cut_from() -> None:
    kb = _library()
    first, _ = _added(kb, PLAN, "report.md")
    _added(kb, "PREFACE ADDED LATER. " + PLAN, "report.md")

    [hit] = [hit for hit in kb.search("intensity", k=5) if hit.chunk.upload == first][
        :1
    ]
    text = kb.text(DEFAULT_SCOPE, first)

    assert text is not None
    assert text[hit.chunk.offset : hit.chunk.offset + len(hit.chunk.text)] == (
        hit.chunk.text
    )


def test_a_field_retrieves_its_own_documents_and_no_others() -> None:
    kb = _library()
    _added(kb, PLAN, "plan.md", FITNESS)
    _added(kb, KYOTO, "kyoto.md", TRAVEL)

    with running_in(frozenset({TRAVEL})):
        hits = kb.search("what do my notes say", k=5)

    assert {hit.chunk.source for hit in hits} == {"kyoto.md"}
    assert all(hit.chunk.scope == TRAVEL for hit in hits)


def test_a_field_is_read_whole_by_name_and_text_in_upload_order() -> None:
    kb = _library()
    _added(kb, PLAN, "plan.md", FITNESS)
    _added(kb, "Rest a week between blocks.", "rest.md", FITNESS)

    with running_in(frozenset({FITNESS})):
        held = kb.all()

    assert [(each.name, each.text) for each in held] == [
        ("plan.md", PLAN),
        ("rest.md", "Rest a week between blocks."),
    ]


def test_two_uploads_of_one_name_are_two_documents() -> None:
    kb = _library()
    for text in LIFTS:
        _added(kb, text, "2026-09-18.md", FITNESS)

    with running_in(frozenset({FITNESS})):
        held = kb.all()

    assert [(each.name, each.text) for each in held] == [
        ("2026-09-18.md", LIFTS[0]),
        ("2026-09-18.md", LIFTS[1]),
    ]
    assert [each.text for each in kb.read(FITNESS, "2026-09-18.md")] == list(LIFTS)
    assert kb.read(FITNESS, "never.md") == []


def test_a_name_whose_file_is_gone_reads_back_the_uploads_still_there() -> None:
    kb = _library()
    documents = kb.documents
    assert isinstance(documents, FakeDocuments)
    gone, _ = _added(kb, LIFTS[0], "2026-09-18.md", FITNESS)
    _added(kb, LIFTS[1], "2026-09-18.md", FITNESS)
    documents.forget(FITNESS, gone)

    assert [each.text for each in kb.read(FITNESS, "2026-09-18.md")] == [LIFTS[1]]
    with running_in(frozenset({FITNESS})):
        assert [each.text for each in kb.all()] == [LIFTS[1]]


def test_a_name_reads_only_the_field_it_is_asked_of() -> None:
    kb = _library()
    _added(kb, PLAN, "plan.md", FITNESS)
    _added(kb, KYOTO, "plan.md", TRAVEL)

    assert [(each.text, each.scope) for each in kb.read(TRAVEL, "plan.md")] == [
        (KYOTO, TRAVEL)
    ]
    with running_in(frozenset({TRAVEL})):
        assert [(each.name, each.scope) for each in kb.all()] == [("plan.md", TRAVEL)]


def test_a_turn_in_two_fields_is_handed_both_each_saying_which() -> None:
    kb = _library()
    _added(kb, PLAN, "plan.md", FITNESS)
    _added(kb, KYOTO, "kyoto.md", TRAVEL)

    with running_in(frozenset({FITNESS, TRAVEL})):
        held = kb.all()

    assert [(each.name, each.scope) for each in held] == [
        ("plan.md", FITNESS),
        ("kyoto.md", TRAVEL),
    ]


class _RecordingRetriever(FakeRetriever):
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


def test_the_index_is_handed_the_span_and_none_of_the_words() -> None:
    retriever = _RecordingRetriever()

    _added(_library(retriever), PLAN, "plan.md", FITNESS)

    assert retriever.given
    assert all(chunk.text == "" for chunk in retriever.given)
    assert sum(chunk.length for chunk in retriever.given) >= len(PLAN)


def test_forgetting_a_document_drops_its_passages_and_its_file() -> None:
    kb = _library()
    documents = kb.documents
    assert isinstance(documents, FakeDocuments)
    upload, _ = _added(kb, PLAN, "plan.md", FITNESS)
    _added(kb, KYOTO, "kyoto.md", FITNESS)

    kb.forget(FITNESS, "plan.md")

    assert kb.list_sources(FITNESS) == ["kyoto.md"]
    assert documents.read(FITNESS, upload) is None
    with running_in(frozenset({FITNESS})):
        assert {hit.chunk.source for hit in kb.search("intensity", k=5)} == {"kyoto.md"}
