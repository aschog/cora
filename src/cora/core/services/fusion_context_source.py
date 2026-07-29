from dataclasses import dataclass
from typing import Protocol

from cora.core.metadata_filter import MetadataFilter
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.query_plan import QueryPlan
from cora.core.services.rank_fusion import reciprocal_rank_fusion


class Planner(Protocol):
    def plan(self, question: str, sources: tuple[str, ...]) -> QueryPlan: ...


class DocumentIndex(Protocol):
    def search(
        self, query: str, k: int, metadata_filter: MetadataFilter | None = None
    ) -> list[RetrievedChunk]: ...

    def list_sources(self) -> list[str]: ...


@dataclass(frozen=True)
class FusionContextSource:
    planner: Planner
    index: DocumentIndex

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        plan = self.planner.plan(query, tuple(self.index.list_sources()))
        rankings = [
            self.index.search(subquery, k, plan.metadata_filter)
            for subquery in plan.queries
        ]
        return reciprocal_rank_fusion(rankings, k)
