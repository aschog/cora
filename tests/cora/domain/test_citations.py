from dataclasses import replace

from cora.domain.chunk import Chunk
from cora.domain.citations import (
    NO_MATCHES,
    CitableHits,
    Citation,
    Nothing,
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


def test_cited_numbers_reads_every_number_in_a_consecutive_run() -> None:
    assert cited_numbers("a balanced diet [3][1][2].") == (3, 1, 2)
    assert cited_numbers("see [10][2].") == (10, 2)


def test_a_citation_is_the_span_a_passage_occupies_in_its_document() -> None:
    context = build_context_block([_hit("a.txt", "alpha", offset=12)])

    assert context.citations == (Citation(1, "a.txt", 12, 17),)


def test_two_passages_of_one_document_are_two_citations() -> None:
    context = build_context_block(
        [_hit("a.txt", "alpha", offset=0), _hit("a.txt", "omega", offset=40)]
    )

    assert context.citations == (
        Citation(1, "a.txt", 0, 5),
        Citation(2, "a.txt", 40, 45),
    )
    assert _numbered(context.text, "a.txt") == ["[1]", "[2]"]


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


def test_numbering_continues_after_the_citations_already_registered() -> None:
    known = (Citation(1, "a.txt", 0, 5), Citation(2, "b.txt", 0, 4))

    context = build_context_block([_hit("c.txt", "gamma")], known)

    assert _numbered(context.text, "c.txt") == ["[3]"]
    assert context.citations == (Citation(3, "c.txt", 0, 5),)


def test_only_the_newly_registered_citations_come_back() -> None:
    known = (Citation(1, "a.txt", 0, 1),)

    context = build_context_block([_hit("a.txt"), _hit("b.txt", "beta")], known)

    assert context.citations == (Citation(2, "b.txt", 0, 4),)


def test_a_passage_already_registered_keeps_its_number() -> None:
    """The same span found again is the same citation: a number the user has already
    been shown may never move to another passage."""
    known = (Citation(1, "a.txt", 0, 5), Citation(2, "b.txt", 10, 14))

    context = build_context_block([_hit("b.txt", "beta", offset=10)], known)

    assert _numbered(context.text, "b.txt") == ["[2]"]
    assert context.citations == ()


def test_the_same_document_at_another_span_is_a_new_citation() -> None:
    known = (Citation(1, "a.txt", 0, 5),)

    context = build_context_block([_hit("a.txt", "omega", offset=40)], known)

    assert context.citations == (Citation(2, "a.txt", 40, 45),)


def test_the_block_is_the_numbered_passages_and_nothing_else() -> None:
    context = build_context_block([_hit("a.txt", "alpha")])

    assert context.text == "[1] a.txt: alpha"


def test_a_hit_list_registers_against_the_citations_known_so_far() -> None:
    known = (Citation(1, "a.txt", 0, 1),)

    context = CitableHits([_hit("b.txt", "beta")]).register(known)

    assert context == build_context_block([_hit("b.txt", "beta")], known)
    assert context.citations == (Citation(2, "b.txt", 0, 4),)


def test_a_hit_list_with_no_hits_says_so_and_adds_nothing() -> None:
    context = CitableHits([]).register(())

    assert "no matching documents" in context.text.lower()
    assert context.citations == ()


def test_a_hit_list_summarises_itself_by_count_and_distinct_source() -> None:
    hits = [_hit("a.txt"), _hit("b.txt"), _hit("a.txt")]

    assert CitableHits(hits).summary == "3 passages from a.txt and b.txt"


def test_a_single_hit_is_one_passage() -> None:
    assert CitableHits([_hit("a.txt")]).summary == "1 passage from a.txt"


def test_a_hit_list_with_no_hits_summarises_as_no_matches() -> None:
    assert CitableHits([]).summary == NO_MATCHES


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


def test_a_number_with_no_registered_citation_is_ignored() -> None:
    known = (Citation(1, "a.txt", 0, 5),)

    assert cited("per [1] and also [9]", known) == (Citation(1, "a.txt", 0, 5),)


def test_a_citation_carries_the_upload_its_passage_was_cut_from() -> None:
    """What makes `[n]` openable: the span is measured in one upload's text, so the
    citation has to name that upload and not merely the file it was called."""
    hit = _hit("a.txt", "alpha", offset=12)
    hit = RetrievedChunk(chunk=replace(hit.chunk, upload="sha-1"), score=1.0)

    context = build_context_block([hit])

    assert context.citations == (Citation(1, "a.txt", 12, 17, upload="sha-1"),)


def test_one_span_of_two_uploads_is_two_citations() -> None:
    """The same filename uploaded twice, edited in between: the spans coincide but the
    text does not, so they may not collapse onto one number — that number would open
    one passage while the answer rested on the other."""
    first = RetrievedChunk(
        chunk=Chunk(text="alpha", source="a.txt", index=0, offset=0, upload="sha-1"),
        score=1.0,
    )
    second = RetrievedChunk(
        chunk=Chunk(text="omega", source="a.txt", index=0, offset=0, upload="sha-2"),
        score=1.0,
    )

    context = build_context_block([first, second])

    assert [(c.number, c.upload) for c in context.citations] == [
        (1, "sha-1"),
        (2, "sha-2"),
    ]
    assert _numbered(context.text, "a.txt") == ["[1]", "[2]"]


def test_an_empty_result_is_read_by_name_and_is_not_a_pair_of_strings() -> None:
    """One absence worded twice, the way every other value in the domain is written.

    A value that compares equal to two strings in the right order offers a reading of
    itself where position says which wording is which — and `ty` refuses the unpacking
    that reading invites, which is the other half of the same statement.
    """
    nothing = Nothing(told="the store is empty", shown="No documents uploaded yet.")

    assert (nothing.told, nothing.shown) == (
        "the store is empty",
        "No documents uploaded yet.",
    )
    assert nothing != ("the store is empty", "No documents uploaded yet.")
