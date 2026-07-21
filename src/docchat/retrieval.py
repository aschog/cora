from dataclasses import dataclass
from typing import Protocol

from docchat.chunk import Chunk


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


class Retriever(Protocol):
    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None: ...

    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]: ...
