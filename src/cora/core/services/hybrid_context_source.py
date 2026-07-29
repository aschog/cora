from dataclasses import dataclass
from typing import Protocol

from cora.core.ports.retrieval import RetrievedChunk
from cora.core.services.rank_fusion import reciprocal_rank_fusion


class SearchIndex(Protocol):
    def search(self, query: str, k: int) -> list[RetrievedChunk]: ...


@dataclass(frozen=True)
class HybridContextSource:
    dense: SearchIndex
    keyword: SearchIndex

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        rankings = [self.dense.search(query, k), self.keyword.search(query, k)]
        return reciprocal_rank_fusion(rankings, k)
