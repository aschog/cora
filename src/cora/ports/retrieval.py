from dataclasses import dataclass
from typing import Protocol

from cora.domain.chunk import Chunk


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


class Retriever(Protocol):
    """The index. A chunk goes in belonging to one upload — `file_hash` — and comes
    back out stamped with it, because a passage's offsets are only meaningful against
    the text that upload arrived as, and the store is the only thing that still knows
    which one that was."""

    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None: ...

    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]: ...

    def sources(self) -> list[str]: ...

    def contains(self, file_hash: str) -> bool: ...
