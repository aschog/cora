"""In-memory fakes of the knowledge-base ports, for the unit tier."""

import hashlib
import math
from dataclasses import dataclass
from typing import NamedTuple

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


class _Record(NamedTuple):
    vector: list[float]
    chunk: Chunk
    file_hash: str


class FakeRetriever:
    def __init__(self) -> None:
        self._records: list[_Record] = []

    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None:
        self._records.extend(
            _Record(vector, chunk, file_hash)
            for chunk, vector in zip(chunks, vectors, strict=True)
        )

    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]:
        ranked = sorted(
            (
                RetrievedChunk(chunk=r.chunk, score=_cosine(query_vector, r.vector))
                for r in self._records
            ),
            key=lambda hit: hit.score,
            reverse=True,
        )
        return ranked[:k]

    def sources(self) -> list[str]:
        return list(dict.fromkeys(r.chunk.source for r in self._records))

    def contains(self, file_hash: str) -> bool:
        return any(r.file_hash == file_hash for r in self._records)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0
