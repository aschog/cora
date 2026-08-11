from dataclasses import dataclass

from cora.core.service_layer.rank_fusion import reciprocal_rank_fusion
from cora.ports.context_source import ContextSource
from cora.ports.retrieval import RetrievedChunk


@dataclass(frozen=True)
class HybridContextSource:
    dense: ContextSource
    keyword: ContextSource

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        rankings = [self.dense.search(query, k), self.keyword.search(query, k)]
        return reciprocal_rank_fusion(rankings, k)
