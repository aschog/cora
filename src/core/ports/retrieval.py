from dataclasses import dataclass
from typing import Protocol

from core.chunk import Chunk


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


class Retriever(Protocol):
    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None: ...

    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]: ...

    def sources(self) -> list[str]: ...

    def contains(self, file_hash: str) -> bool: ...
