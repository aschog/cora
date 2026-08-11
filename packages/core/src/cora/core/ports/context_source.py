from typing import Protocol

from cora.core.ports.retrieval import RetrievedChunk


class ContextSource(Protocol):
    def search(self, query: str, k: int) -> list[RetrievedChunk]: ...
