from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.scoping import running_in
from cora.plugins.documents import extend
from cora.ports.host import HANDLER, Handler
from fakes import FakeDocuments, FakeEmbedder, FakeFiles, FakeRetriever, host_for
from pdf_fixtures import make_pdf_bytes

FIELD = "travel"
MAPLES = b"The maples turn in the second week of November."


def _library() -> KnowledgeBase:
    return KnowledgeBase(
        embedder=FakeEmbedder(), retriever=FakeRetriever(), documents=FakeDocuments()
    )


def _hearing(files: FakeFiles, library: KnowledgeBase) -> Handler:
    host = host_for(
        "cora.plugins.documents", files=files, documents=library, indexing=library
    )
    extend(host)
    [handler] = [e.value for e in host.registered if e.kind == HANDLER]
    return handler.handle


def _landed(name: str, data: bytes, library: KnowledgeBase) -> str | None:
    files = FakeFiles({(FIELD, name): data})
    with running_in(frozenset({FIELD})):
        return _hearing(files, library)(name)


def test_a_markdown_upload_is_indexed_into_its_field_and_found_there() -> None:
    library = _library()

    refused = _landed("kyoto.md", MAPLES, library)

    assert refused is None
    with running_in(frozenset({FIELD})):
        [hit] = library.search("maples", 1)
    assert hit.chunk.text == MAPLES.decode()
    assert library.list_sources(FIELD) == ["kyoto.md"]
    assert library.list_sources("fitness") == []


def test_plain_text_and_pdf_are_read_and_another_kind_is_left_alone() -> None:
    library = _library()

    assert _landed("plan.txt", b"Squats on Tuesday.", library) is None
    assert _landed("scan.pdf", make_pdf_bytes("Third page."), library) is None
    assert _landed("sheet.xlsx", b"PK\x03\x04", library) is None

    assert library.list_sources(FIELD) == ["plan.txt", "scan.pdf"]


def test_an_empty_document_and_one_over_the_cap_are_refused_with_their_sentences() -> (
    None
):
    library = _library()

    empty = _landed("blank.txt", b"  \n\t ", library)
    huge = _landed("huge.txt", b"x" * (10 * 1024 * 1024 + 1), library)

    assert empty is not None and "no readable text" in empty
    assert huge is not None and "too large" in huge
    assert library.list_sources(FIELD) == []


def test_the_same_bytes_twice_add_nothing_and_a_missing_text_is_repaired() -> None:
    library = _library()
    documents = library.documents
    assert isinstance(documents, FakeDocuments)

    _landed("kyoto.md", MAPLES, library)
    _landed("kyoto.md", MAPLES, library)
    assert documents.writes == 1
    assert library.list_sources(FIELD) == ["kyoto.md"]

    with running_in(frozenset({FIELD})):
        [hit] = library.search("maples", 1)
    documents.forget(FIELD, hit.chunk.upload)
    _landed("kyoto.md", MAPLES, library)

    assert documents.writes == 2
    assert library.text(FIELD, hit.chunk.upload) == MAPLES.decode()


def test_a_kind_it_cannot_read_is_left_alone_rather_than_refused() -> None:
    library = _library()

    ignored = _landed("rows.csv", b"a,b\n1,2\n", library)

    assert ignored is None, "a plugin that cannot read a file does not veto the upload"
    assert library.list_sources(FIELD) == []


def test_a_kind_it_reads_and_cannot_is_still_refused() -> None:
    library = _library()

    refused = _landed("blank.md", b"   \n\t ", library)

    assert refused is not None and "no readable text" in refused
