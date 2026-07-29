from cora.core.chunk import Chunk
from cora.core.ports.retrieval import RetrievedChunk

RRF_C = 60


def reciprocal_rank_fusion(
    rankings: list[list[RetrievedChunk]], k: int, c: int = RRF_C
) -> list[RetrievedChunk]:
    scores: dict[Chunk, float] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            scores[hit.chunk] = scores.get(hit.chunk, 0.0) + 1.0 / (c + rank)
    fused = [
        RetrievedChunk(chunk=chunk, score=score) for chunk, score in scores.items()
    ]
    fused.sort(key=lambda hit: hit.score, reverse=True)
    return fused[:k]
