from dataclasses import dataclass
from typing import Protocol

from cora.domain.metadata_filter import MetadataFilter
from cora.domain.query_plan import QueryPlan
from cora.engine.rank_fusion import reciprocal_rank_fusion
from cora.ports.retrieval import RetrievedChunk


class Planner(Protocol):
    def plan(self, question: str, sources: tuple[str, ...]) -> QueryPlan: ...


class SelfQueryIndex(Protocol):
    def search(
        self, query: str, k: int, metadata_filter: MetadataFilter | None = None
    ) -> list[RetrievedChunk]: ...

    def list_sources(self) -> list[str]: ...


@dataclass(frozen=True)
class FusionContextSource:
    planner: Planner
    index: SelfQueryIndex

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        plan = self.planner.plan(query, tuple(self.index.list_sources()))
        rankings = [
            self.index.search(subquery, k, plan.metadata_filter)
            for subquery in plan.queries
        ]
        return reciprocal_rank_fusion(rankings, k)
