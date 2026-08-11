"""In-memory fakes of the ports and stubs of the plugin contract, for the unit tier."""

import hashlib
import math
from dataclasses import dataclass, field
from typing import NamedTuple

from cora.core.domain.chunk import Chunk
from cora.core.domain.metadata_filter import MetadataFilter
from cora.core.ports.chat_model import Message, ModelReply
from cora.core.ports.plugin import Tool
from cora.core.ports.retrieval import RetrievedChunk


def _add(a: int, b: int) -> int:
    return a + b


def add_tool() -> Tool:
    return Tool(
        name="add",
        description="Add two integers.",
        parameter_schema={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
        run=_add,
    )


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

    def query(
        self,
        query_vector: list[float],
        k: int,
        metadata_filter: MetadataFilter | None = None,
    ) -> list[RetrievedChunk]:
        records = [r for r in self._records if _matches(r.chunk, metadata_filter)]
        ranked = sorted(
            (
                RetrievedChunk(chunk=r.chunk, score=_cosine(query_vector, r.vector))
                for r in records
            ),
            key=lambda hit: hit.score,
            reverse=True,
        )
        return ranked[:k]

    def sources(self) -> list[str]:
        return list(dict.fromkeys(r.chunk.source for r in self._records))

    def contains(self, file_hash: str) -> bool:
        return any(r.file_hash == file_hash for r in self._records)


def _matches(chunk: Chunk, metadata_filter: MetadataFilter | None) -> bool:
    if metadata_filter is None:
        return True
    return getattr(chunk, metadata_filter.field) == metadata_filter.value


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


class ScriptedChatModel:
    def __init__(self, replies: list[ModelReply]) -> None:
        self._replies = list(replies)
        self.last_messages: tuple[Message, ...] | None = None
        self.last_tools: tuple[Tool, ...] | None = None

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.last_messages = messages
        self.last_tools = tools
        return self._replies.pop(0)


class CountingRetriever(FakeRetriever):
    """Counts searches, so a test can show that a turn never reached the store."""

    def __init__(self) -> None:
        super().__init__()
        self.queries = 0

    def query(
        self,
        query_vector: list[float],
        k: int,
        metadata_filter: MetadataFilter | None = None,
    ) -> list[RetrievedChunk]:
        self.queries += 1
        return super().query(query_vector, k, metadata_filter)


@dataclass
class FailingEmbedder:
    error: Exception

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise self.error


@dataclass
class FailingRetriever:
    error: Exception

    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None:
        raise self.error

    def query(
        self,
        query_vector: list[float],
        k: int,
        metadata_filter: MetadataFilter | None = None,
    ) -> list[RetrievedChunk]:
        raise self.error

    def sources(self) -> list[str]:
        raise self.error

    def contains(self, file_hash: str) -> bool:
        raise self.error


@dataclass
class FailingChatModel:
    error: Exception

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        raise self.error


@dataclass
class FakeContextSource:
    results: list[RetrievedChunk] = field(default_factory=list)
    last_query: str | None = None
    last_k: int | None = None

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        self.last_query = query
        self.last_k = k
        return self.results
