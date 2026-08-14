from rank_bm25 import BM25Okapi

from cora.domain.chunk import Chunk
from cora.ports.retrieval import RetrievedChunk


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


class Bm25KeywordIndex:
    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._corpus: list[list[str]] = []
        self._bm25: BM25Okapi | None = None

    @classmethod
    def from_chunks(cls, chunks: list[Chunk]) -> "Bm25KeywordIndex":
        index = cls()
        index.add(chunks)
        return index

    def add(self, chunks: list[Chunk]) -> None:
        self._chunks.extend(chunks)
        self._corpus.extend(_tokenize(chunk.text) for chunk in chunks)
        if not self._chunks:
            return
        self._bm25 = BM25Okapi(self._corpus)

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        tokens = _tokenize(query)
        if self._bm25 is None or not tokens:
            return []
        terms = set(tokens)
        scores = self._bm25.get_scores(tokens)
        matched = [i for i, doc in enumerate(self._corpus) if terms & set(doc)]
        matched.sort(key=lambda i: (-scores[i], i))
        return [
            RetrievedChunk(chunk=self._chunks[i], score=float(scores[i]))
            for i in matched[:k]
        ]
