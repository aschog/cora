from cora.core.chunk import Chunk
from cora.core.citations import Source, build_context_block, cited_numbers
from cora.core.ports.retrieval import RetrievedChunk


def _hit(source: str, text: str = "t") -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(text=text, source=source, index=0, offset=0), score=1.0
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


def test_a_batch_numbers_from_one_per_unique_source() -> None:
    context = build_context_block(
        [_hit("a.txt", "alpha1"), _hit("b.txt", "beta"), _hit("a.txt", "alpha2")]
    )

    assert context.sources == (Source(1, "a.txt"), Source(2, "b.txt"))
    assert _numbered(context.text, "a.txt") == ["[1]", "[1]"]
    assert _numbered(context.text, "b.txt") == ["[2]"]
    assert "alpha1" in context.text and "alpha2" in context.text


def test_numbering_continues_after_the_sources_already_registered() -> None:
    known = (Source(1, "a.txt"), Source(2, "b.txt"))

    context = build_context_block([_hit("c.txt", "gamma")], known)

    assert _numbered(context.text, "c.txt") == ["[3]"]


def test_only_the_newly_registered_sources_come_back() -> None:
    known = (Source(1, "a.txt"),)

    context = build_context_block([_hit("a.txt"), _hit("b.txt")], known)

    assert context.sources == (Source(2, "b.txt"),)


def test_an_already_registered_source_keeps_its_number() -> None:
    known = (Source(1, "a.txt"), Source(2, "b.txt"))

    context = build_context_block([_hit("b.txt", "beta")], known)

    assert _numbered(context.text, "b.txt") == ["[2]"]
    assert context.sources == ()


def test_the_block_marks_its_document_text_as_untrusted_data() -> None:
    context = build_context_block([_hit("a.txt", "alpha")])

    notice, _, body = context.text.partition("[1]")

    assert "untrusted" in notice.lower()
    assert "instructions" in notice.lower()
    assert "alpha" in body
