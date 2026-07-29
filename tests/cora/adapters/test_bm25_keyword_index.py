from collections.abc import Callable

from cora.adapters.bm25_keyword_index import Bm25KeywordIndex
from cora.core.chunk import Chunk


def test_search_ranks_the_lexical_match_first(
    make_chunk: Callable[..., Chunk],
) -> None:
    match = make_chunk("protein supports muscle growth and repair", index=0)
    unrelated = make_chunk("hydration and water intake during exercise", index=1)
    another = make_chunk("sleep is important for recovery", index=2)
    index = Bm25KeywordIndex.from_chunks([unrelated, another, match])

    hits = index.search("protein muscle", k=3)

    assert hits[0].chunk == match


def test_search_reconstructs_the_chunk_with_identical_fields(
    make_chunk: Callable[..., Chunk],
) -> None:
    chunk = make_chunk("unique zebra token", source="notes.md", index=7, offset=42)
    index = Bm25KeywordIndex.from_chunks([chunk])

    [hit] = index.search("zebra", k=1)

    assert hit.chunk == chunk
    assert (hit.chunk.text, hit.chunk.source, hit.chunk.index, hit.chunk.offset) == (
        "unique zebra token",
        "notes.md",
        7,
        42,
    )


def test_from_chunks_seeds_the_whole_corpus_searchable(
    make_chunk: Callable[..., Chunk],
) -> None:
    corpus = [
        make_chunk("protein for muscle", index=0),
        make_chunk("hydration and water", index=1),
        make_chunk("sleep for recovery", index=2),
    ]
    index = Bm25KeywordIndex.from_chunks(corpus)

    for token, expected in [
        ("protein", corpus[0]),
        ("water", corpus[1]),
        ("sleep", corpus[2]),
    ]:
        assert index.search(token, k=1)[0].chunk == expected


def test_a_second_add_keeps_earlier_chunks_searchable(
    make_chunk: Callable[..., Chunk],
) -> None:
    first = make_chunk("protein for muscle", source="a.md", index=0)
    index = Bm25KeywordIndex.from_chunks([first])

    index.add([make_chunk("hydration and water", source="b.md", index=0)])

    assert index.search("protein", k=1)[0].chunk == first
