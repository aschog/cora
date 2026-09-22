from dataclasses import replace

from cora.domain.chunk import Chunk
from cora.domain.citations import (
    CitableHits,
    Citation,
    build_context_block,
    cited,
    cited_numbers,
)
from cora.ports.retrieval import RetrievedChunk


def _hit(source: str, text: str = "t", offset: int = 0) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(text=text, source=source, index=0, offset=offset), score=1.0
    )


def _numbered(context_text: str, name: str) -> list[str]:
    return [line[:3] for line in context_text.splitlines() if name in line]


def test_cited_numbers_are_distinct_in_order_of_first_appearance() -> None:
    assert cited_numbers("uses [3], then [1], and [3] again") == (3, 1)
    assert cited_numbers("no brackets here") == ()


def test_cited_numbers_ignores_brackets_glued_to_a_word_or_bracket() -> None:
    assert cited_numbers("write list[2] or arr[0][1], then cite [1]") == (1,)


def test_a_citation_is_the_span_a_passage_occupies_in_its_document() -> None:
    context = build_context_block([_hit("a.txt", "alpha", offset=12)])

    assert context.citations == (Citation(1, "a.txt", 12, 17),)


def test_a_batch_numbers_every_passage_in_the_order_it_came_back() -> None:
    context = build_context_block(
        [
            _hit("a.txt", "alpha1", offset=0),
            _hit("b.txt", "beta", offset=0),
            _hit("a.txt", "alpha2", offset=30),
        ]
    )

    assert [citation.number for citation in context.citations] == [1, 2, 3]
    assert _numbered(context.text, "a.txt") == ["[1]", "[3]"]
    assert _numbered(context.text, "b.txt") == ["[2]"]


def test_a_passage_already_registered_keeps_its_number() -> None:
    known = (Citation(1, "a.txt", 0, 5), Citation(2, "b.txt", 10, 14))

    context = build_context_block([_hit("b.txt", "beta", offset=10)], known)

    assert _numbered(context.text, "b.txt") == ["[2]"]
    assert context.citations == ()


def test_the_same_document_at_another_span_is_a_new_citation() -> None:
    known = (Citation(1, "a.txt", 0, 5),)

    context = build_context_block([_hit("a.txt", "omega", offset=40)], known)

    assert context.citations == (Citation(2, "a.txt", 40, 45),)


def test_a_hit_list_registers_against_the_citations_known_so_far() -> None:
    known = (Citation(1, "a.txt", 0, 1),)

    context = CitableHits([_hit("b.txt", "beta")]).register(known)

    assert context == build_context_block([_hit("b.txt", "beta")], known)
    assert context.citations == (Citation(2, "b.txt", 0, 4),)


def test_a_hit_list_summarises_itself_by_count_and_distinct_source() -> None:
    hits = [_hit("a.txt"), _hit("b.txt"), _hit("a.txt")]

    assert CitableHits(hits).summary == "3 passages from a.txt and b.txt"


def test_only_the_cited_passages_come_back_in_ascending_order() -> None:
    citations = (
        Citation(1, "a.txt", 0, 5),
        Citation(2, "b.txt", 0, 4),
        Citation(3, "c.txt", 0, 5),
    )

    assert cited("first [3], then [1].", citations) == (
        Citation(1, "a.txt", 0, 5),
        Citation(3, "c.txt", 0, 5),
    )


def test_a_citation_carries_the_upload_its_passage_was_cut_from() -> None:
    hit = _hit("a.txt", "alpha", offset=12)
    hit = RetrievedChunk(chunk=replace(hit.chunk, upload="sha-1"), score=1.0)

    context = build_context_block([hit])

    assert context.citations == (Citation(1, "a.txt", 12, 17, upload="sha-1"),)


def test_a_payload_renders_itself_for_a_reader_that_cannot_cite() -> None:
    hits = CitableHits([_hit("plan.md", "Steps:\nwarm up\nsquat")])

    assert hits.unnumbered() == "plan.md: Steps:\nwarm up\nsquat"
