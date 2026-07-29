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
    seen_sources: tuple[str, ...] | None = None

    def plan(self, question: str, sources: tuple[str, ...]) -> QueryPlan:
        self.seen_sources = sources
        return self.result


@dataclass
class FakeDocumentIndex:
    rankings: dict[str, list[RetrievedChunk]]
    sources: list[str] = field(default_factory=list)
    calls: list[tuple[str, int, MetadataFilter | None]] = field(default_factory=list)

    def search(
        self, query: str, k: int, metadata_filter: MetadataFilter | None = None
    ) -> list[RetrievedChunk]:
        self.calls.append((query, k, metadata_filter))
        return self.rankings.get(query, [])

    def list_sources(self) -> list[str]:
        return self.sources


def test_fusion_plans_fans_out_and_fuses(make_chunk: Callable[..., Chunk]) -> None:
    a = make_chunk("a", index=0)
    b = make_chunk("b", index=1)
    planner = FakePlanner(QueryPlan(queries=("q1", "q2")))
    index = FakeDocumentIndex(
        rankings={
            "q1": [
                RetrievedChunk(chunk=a, score=0.0),
                RetrievedChunk(chunk=b, score=0.0),
            ],
            "q2": [RetrievedChunk(chunk=a, score=0.0)],
        },
        sources=["doc.txt"],
    )
    fusion = FusionContextSource(planner=planner, index=index)

    hits = fusion.search("question", k=10)

    assert [hit.chunk for hit in hits] == [a, b]
    assert [call[0] for call in index.calls] == ["q1", "q2"]
    assert planner.seen_sources == ("doc.txt",)


def test_fusion_passes_the_plan_filter_into_every_search() -> None:
    metadata_filter = MetadataFilter(field="source", value="protein.md")
    planner = FakePlanner(
        QueryPlan(queries=("q1", "q2"), metadata_filter=metadata_filter)
    )
    index = FakeDocumentIndex(rankings={}, sources=["protein.md"])
    fusion = FusionContextSource(planner=planner, index=index)

    fusion.search("question", k=5)

    assert [call[2] for call in index.calls] == [metadata_filter, metadata_filter]


def test_fusion_degrades_to_a_single_plain_search_on_a_fallback_plan(
    make_chunk: Callable[..., Chunk],
) -> None:
    a = make_chunk("a", index=0)
    planner = FakePlanner(QueryPlan(queries=("original question",)))
    index = FakeDocumentIndex(
        rankings={"original question": [RetrievedChunk(chunk=a, score=0.0)]}
    )
    fusion = FusionContextSource(planner=planner, index=index)

    hits = fusion.search("original question", k=10)

    assert [hit.chunk for hit in hits] == [a]
    assert index.calls == [("original question", 10, None)]
