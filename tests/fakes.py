"""In-memory fakes of the knowledge-base ports, for the unit tier."""

import hashlib
from dataclasses import dataclass

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
    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]:
        return []
