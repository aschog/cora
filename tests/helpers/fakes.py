"""In-memory fakes of the ports and stubs of the plugin contract, for the unit tier."""

import hashlib
import math
from dataclasses import dataclass, field, replace
from typing import NamedTuple

from cora.domain.chunk import Chunk
from cora.domain.errors import DocumentStoreError, MemoryStoreError
from cora.ports.chat_model import Message, ModelReply
from cora.ports.loading import Loaders
from cora.ports.memory import Fact
from cora.ports.plugin import Tool
from cora.ports.retrieval import RetrievedChunk


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
        """Stamped with the upload on the way in, as the real index does: a hit carries
        the upload its offsets were measured in."""
        self._records.extend(
            _Record(vector, replace(chunk, upload=file_hash), file_hash)
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


class ScriptedChatModel:
    def __init__(self, replies: list[ModelReply]) -> None:
        self._replies = list(replies)
        self.last_messages: tuple[Message, ...] | None = None
        self.last_tools: tuple[Tool, ...] | None = None
        self.completions = 0

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.last_messages = messages
        self.last_tools = tools
        self.completions += 1
        return self._replies.pop(0)


class CountingRetriever(FakeRetriever):
    """Counts searches, so a test can show that a turn never reached the store."""

    def __init__(self) -> None:
        super().__init__()
        self.queries = 0

    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]:
        self.queries += 1
        return super().query(query_vector, k)


class FakeDocuments:
    """The kept text, in a dict, keyed by upload as the real store is. `writes` is what
    lets a test say a document was kept once, or not at all."""

    def __init__(self) -> None:
        self._kept: dict[str, str] = {}
        self.writes = 0

    def keep(self, upload: str, text: str) -> None:
        self._kept[upload] = text
        self.writes += 1

    def read(self, upload: str) -> str | None:
        return self._kept.get(upload)


class KeepsNothingDocuments(FakeDocuments):
    """A store that accepts and forgets: what an index written before cora kept any
    document text looks like from the outside."""

    def keep(self, upload: str, text: str) -> None:
        return None


class FailingDocuments(FakeDocuments):
    def read(self, upload: str) -> str | None:
        raise DocumentStoreError


class FakeMemory:
    def __init__(self, facts: tuple[str, ...] = ()) -> None:
        self._facts: list[Fact] = []
        for text in facts:
            self.remember(text)

    def remember(self, text: str) -> None:
        self._facts.append(Fact(key=f"f{len(self._facts) + 1}", text=text))

    def recall(self) -> tuple[Fact, ...]:
        return tuple(self._facts)

    def forget(self, key: str) -> None:
        self._facts = [fact for fact in self._facts if fact.key != key]

    def clear(self) -> None:
        self._facts.clear()


@dataclass
class ReadOnlyMemory:
    """Recalls what it holds and fails every write: the shape of a store that went
    away mid-session, which is when the sidebar's buttons are already on screen."""

    facts: tuple[str, ...] = ()
    error: Exception = field(default_factory=MemoryStoreError)

    def __post_init__(self) -> None:
        self._readable = FakeMemory(self.facts)

    def remember(self, text: str) -> None:
        raise self.error

    def recall(self) -> tuple[Fact, ...]:
        return self._readable.recall()

    def forget(self, key: str) -> None:
        raise self.error

    def clear(self) -> None:
        raise self.error


@dataclass
class FailingMemory:
    error: Exception

    def remember(self, text: str) -> None:
        raise self.error

    def recall(self) -> tuple[Fact, ...]:
        raise self.error

    def forget(self, key: str) -> None:
        raise self.error

    def clear(self) -> None:
        raise self.error


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

    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]:
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


def _decode(data: bytes, filename: str) -> str:
    return data.decode("utf-8")


TEXT_LOADERS: Loaders = {".txt": _decode, ".md": _decode}
"""What most tests need: no PDF, so no reason to reach for the real registry."""
