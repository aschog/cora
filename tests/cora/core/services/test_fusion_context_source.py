from collections.abc import Callable
from dataclasses import dataclass, field

from cora.core.chunk import Chunk
from cora.core.metadata_filter import MetadataFilter
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.query_plan import QueryPlan
from cora.core.services.fusion_context_source import FusionContextSource


@dataclass
class FakePlanner:
    result: QueryPlan

    def plan(self, question: str, sources: tuple[str, ...]) -> QueryPlan:
        return self.result


@dataclass
class FakeSelfQueryIndex:
    rankings: dict[str, list[RetrievedChunk]]
    sources: list[str] = field(default_factory=list)

    def search(
        self, query: str, k: int, metadata_filter: MetadataFilter | None = None
    ) -> list[RetrievedChunk]:
        hits = self.rankings.get(query, [])
        if metadata_filter is not None:
            hits = [
                hit
                for hit in hits
                if getattr(hit.chunk, metadata_filter.field) == metadata_filter.value
            ]
        return hits[:k]

    def list_sources(self) -> list[str]:
        return self.sources


def test_fusion_fans_out_across_sub_queries_and_fuses(
    make_chunk: Callable[..., Chunk],
) -> None:
    shared = make_chunk("shared", index=0)
    only_first = make_chunk("only_first", index=1)
    only_second = make_chunk("only_second", index=2)
    planner = FakePlanner(QueryPlan(queries=("q1", "q2")))
    index = FakeSelfQueryIndex(
        rankings={
            "q1": [
                RetrievedChunk(chunk=shared, score=0.0),
                RetrievedChunk(chunk=only_first, score=0.0),
            ],
            "q2": [
                RetrievedChunk(chunk=shared, score=0.0),
                RetrievedChunk(chunk=only_second, score=0.0),
            ],
        }
    )
    fusion = FusionContextSource(planner=planner, index=index)

    chunks = [hit.chunk for hit in fusion.search("question", k=10)]

    assert set(chunks) == {shared, only_first, only_second}
    assert chunks[0] == shared


def test_fusion_narrows_results_to_the_plan_filter(
    make_chunk: Callable[..., Chunk],
) -> None:
    protein = make_chunk("p", source="protein.md", index=0)
    energy = make_chunk("e", source="energy.md", index=0)
    metadata_filter = MetadataFilter(field="source", value="protein.md")
    planner = FakePlanner(QueryPlan(queries=("q1",), metadata_filter=metadata_filter))
    index = FakeSelfQueryIndex(
        rankings={
            "q1": [
                RetrievedChunk(chunk=protein, score=0.0),
                RetrievedChunk(chunk=energy, score=0.0),
            ]
        }
    )
    fusion = FusionContextSource(planner=planner, index=index)

    chunks = [hit.chunk for hit in fusion.search("question", k=10)]

    assert chunks == [protein]


def test_fusion_returns_an_unfiltered_search_for_a_fallback_plan(
    make_chunk: Callable[..., Chunk],
) -> None:
    protein = make_chunk("p", source="protein.md", index=0)
    energy = make_chunk("e", source="energy.md", index=0)
    planner = FakePlanner(QueryPlan(queries=("original question",)))
    index = FakeSelfQueryIndex(
        rankings={
            "original question": [
                RetrievedChunk(chunk=protein, score=0.0),
                RetrievedChunk(chunk=energy, score=0.0),
            ]
        }
    )
    fusion = FusionContextSource(planner=planner, index=index)

    chunks = {hit.chunk for hit in fusion.search("original question", k=10)}

    assert chunks == {protein, energy}
