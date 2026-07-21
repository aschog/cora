"""In-memory fakes of the knowledge-base ports, for the unit tier."""

import hashlib
import math
from dataclasses import dataclass

from docchat.chunk import Chunk
from docchat.retrieval import RetrievedChunk


@dataclass
class FakeEmbedder:
    dim: int = 16

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [digest[i % len(digest)] / 255.0 for i in range(self.dim)]


class FakeRetriever:
    def __init__(self) -> None:
        self._records: list[tuple[list[float], Chunk, str]] = []

    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None:
        self._records.extend(
            (vector, chunk, file_hash)
            for chunk, vector in zip(chunks, vectors, strict=True)
        )

    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]:
        ranked = sorted(
            (
                RetrievedChunk(chunk=chunk, score=_cosine(query_vector, vector))
                for vector, chunk, _ in self._records
            ),
            key=lambda hit: hit.score,
            reverse=True,
        )
        return ranked[:k]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0
