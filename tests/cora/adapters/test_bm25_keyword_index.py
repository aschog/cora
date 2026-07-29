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
