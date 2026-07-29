from dataclasses import dataclass

from cora.core.chunk import Chunk
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.services.hybrid_context_source import HybridContextSource


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
