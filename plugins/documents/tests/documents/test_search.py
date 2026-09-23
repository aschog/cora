from cora.domain.chunk import Chunk
from cora.domain.citations import CitableHits
from cora.plugins.documents.search import EMPTY_STORE, DocumentSearch
from cora.ports.retrieval import RetrievedChunk
from fakes import FakeContextSource


def _hit(source: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(text=text, source=source, index=0, offset=0), score=1.0
    )


def test_the_tool_searches_its_source_and_numbers_the_hits_to_be_cited() -> None:
    hits = [_hit("note.md", "protein builds muscle")]
    source = FakeContextSource(hits)

    payload = DocumentSearch(source, top_k=4)("protein")

    assert (source.last_query, source.last_k) == ("protein", 4)
    assert payload == CitableHits(hits, nothing=EMPTY_STORE)
    assert "[1]" in payload.register(known=()).text


def test_a_search_of_an_empty_field_says_nothing_was_uploaded() -> None:
    payload = DocumentSearch(FakeContextSource([]), top_k=4)("protein")

    assert payload.register(known=()).text == EMPTY_STORE.told
    assert payload.summary == EMPTY_STORE.shown
