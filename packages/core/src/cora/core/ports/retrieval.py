from dataclasses import dataclass
from typing import Protocol

from cora.core.domain.chunk import Chunk
from cora.core.domain.metadata_filter import MetadataFilter


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


class Retriever(Protocol):
    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None: ...

    def query(
        self,
        query_vector: list[float],
        k: int,
        metadata_filter: MetadataFilter | None = None,
    ) -> list[RetrievedChunk]: ...

    def sources(self) -> list[str]: ...

    def contains(self, file_hash: str) -> bool: ...
