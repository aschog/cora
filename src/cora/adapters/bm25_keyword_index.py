from rank_bm25 import BM25Okapi

from cora.core.chunk import Chunk
from cora.core.ports.retrieval import RetrievedChunk


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


class Bm25KeywordIndex:
    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._bm25: BM25Okapi | None = None

    @classmethod
    def from_chunks(cls, chunks: list[Chunk]) -> "Bm25KeywordIndex":
        index = cls()
        index.add(chunks)
        return index

    def add(self, chunks: list[Chunk]) -> None:
        self._chunks.extend(chunks)
        if not self._chunks:
            return
        self._bm25 = BM25Okapi([_tokenize(chunk.text) for chunk in self._chunks])

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(range(len(self._chunks)), key=lambda i: (-scores[i], i))
        return [
            RetrievedChunk(chunk=self._chunks[i], score=float(scores[i]))
            for i in ranked[:k]
        ]
