from collections.abc import Callable

import pytest

from cora.core.service_layer.rank_fusion import reciprocal_rank_fusion
from cora.domain.chunk import Chunk
from cora.ports.retrieval import RetrievedChunk


def test_rrf_orders_by_summed_reciprocal_rank_with_c_60(
    make_chunk: Callable[..., Chunk],
) -> None:
    a = make_chunk("a", index=0)
    b = make_chunk("b", index=1)
    ranking = [RetrievedChunk(chunk=a, score=0.0), RetrievedChunk(chunk=b, score=0.0)]

    fused = reciprocal_rank_fusion([ranking, ranking], k=10)

    assert [hit.chunk for hit in fused] == [a, b]
    assert fused[0].score == pytest.approx(2 / 61)


def test_rrf_ranks_a_chunk_in_many_lists_above_one_in_a_single_list(
    make_chunk: Callable[..., Chunk],
) -> None:
    shared = make_chunk("shared", index=0)
    lonely = make_chunk("lonely", index=1)
    first = [
        RetrievedChunk(chunk=lonely, score=0.0),
        RetrievedChunk(chunk=shared, score=0.0),
    ]
    second = [RetrievedChunk(chunk=shared, score=0.0)]

    fused = reciprocal_rank_fusion([first, second], k=10)

    assert fused[0].chunk == shared


def test_rrf_caps_the_result_at_top_k(make_chunk: Callable[..., Chunk]) -> None:
    ranking = [
        RetrievedChunk(chunk=make_chunk(str(i), index=i), score=0.0) for i in range(5)
    ]

    fused = reciprocal_rank_fusion([ranking], k=2)

    assert len(fused) == 2
