from dataclasses import dataclass

from cora.core.service_layer.hybrid_context_source import HybridContextSource
from cora.domain.chunk import Chunk
from cora.ports.retrieval import RetrievedChunk


@dataclass
class FakeIndex:
    hits: list[RetrievedChunk]

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        return self.hits[:k]


def _chunk(text: str) -> Chunk:
    return Chunk(text=text, source=text, index=0, offset=0)


def test_search_fuses_dense_and_keyword_rankings() -> None:
    a, b, c = _chunk("a"), _chunk("b"), _chunk("c")
    dense = FakeIndex([RetrievedChunk(a, 0.9), RetrievedChunk(b, 0.8)])
    keyword = FakeIndex([RetrievedChunk(c, 5.0), RetrievedChunk(a, 3.0)])
    source = HybridContextSource(dense=dense, keyword=keyword)

    hits = source.search("q", k=3)

    assert hits[0].chunk == a


def test_search_caps_the_fused_result_at_k() -> None:
    dense = FakeIndex(
        [RetrievedChunk(_chunk(f"d{i}"), 1.0 - i * 0.1) for i in range(5)]
    )
    keyword = FakeIndex([RetrievedChunk(_chunk(f"k{i}"), 5.0 - i) for i in range(5)])
    source = HybridContextSource(dense=dense, keyword=keyword)

    hits = source.search("q", k=3)

    sources = {hit.chunk.source for hit in hits}
    assert len(hits) == 3
    assert sources & {"d0", "d1", "d2"}
    assert sources & {"k0", "k1", "k2"}
