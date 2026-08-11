from dataclasses import dataclass

from cora.core.context_source import ContextSource
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.services.rank_fusion import reciprocal_rank_fusion


@dataclass(frozen=True)
class HybridContextSource:
    dense: ContextSource
    keyword: ContextSource

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        rankings = [self.dense.search(query, k), self.keyword.search(query, k)]
        return reciprocal_rank_fusion(rankings, k)
