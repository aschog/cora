"""In-memory fakes of the ports and stubs of the plugin contract, for the unit tier."""

import hashlib
import math
from dataclasses import dataclass, field, replace
from typing import Any, NamedTuple

from cora.domain.chunk import Chunk
from cora.domain.conversation import Session, Turn
from cora.domain.errors import (
    ConversationStoreError,
    DocumentStoreError,
    MemoryStoreError,
)
from cora.engine.host import PluginHost
from cora.ports.chat_model import (
    ChatModel,
    Message,
    ModelReply,
    Piece,
    TextSink,
    unheard,
)
from cora.ports.context_source import ContextSource
from cora.ports.loading import Loaders
from cora.ports.memory import Fact, Memory
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
    scope: str


class FakeRetriever:
    """One list, read a field at a time, as the real index is a collection per field.
    The stored chunk carries no text, because the index keeps the span alone."""

    def __init__(self) -> None:
        self._records: list[_Record] = []

    def add(
        self,
        scope: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
        file_hash: str,
    ) -> None:
        """Stamped with the upload and the field on the way in, as the real index does:
        a hit carries the upload its offsets were measured in, and the field whose
        directory that text is kept under."""
        self._records.extend(
            _Record(
                vector,
                replace(chunk, text="", upload=file_hash, scope=scope),
                file_hash,
                scope,
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        )

    def query(
        self, scope: str, query_vector: list[float], k: int
    ) -> list[RetrievedChunk]:
        ranked = sorted(
            (
                RetrievedChunk(chunk=r.chunk, score=_cosine(query_vector, r.vector))
                for r in self._records
                if r.scope == scope
            ),
            key=lambda hit: hit.score,
            reverse=True,
        )
        return ranked[:k]

    def sources(self, scope: str) -> list[str]:
        return list(
            dict.fromkeys(r.chunk.source for r in self._records if r.scope == scope)
        )

    def contains(self, scope: str, file_hash: str) -> bool:
        return any(r.file_hash == file_hash and r.scope == scope for r in self._records)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


class ScriptedChatModel:
    """`pieces` is how each reply is written, one list per reply. Left out, a reply is
    written in one piece — a real model writes whatever it returns, so a fake that
    returned text and wrote none of it would let a sink go untested by accident."""

    def __init__(
        self, replies: list[ModelReply], pieces: list[list[str]] | None = None
    ) -> None:
        self._replies = list(replies)
        self._pieces = [list(each) for each in pieces] if pieces is not None else None
        self.last_messages: tuple[Message, ...] | None = None
        self.last_tools: tuple[Tool, ...] | None = None
        self.completions = 0

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        self.last_messages = messages
        self.last_tools = tools
        self.completions += 1
        reply = self._replies.pop(0)
        written = self._pieces.pop(0) if self._pieces is not None else [reply.text]
        for piece in written:
            if piece:
                on_text(Piece(piece))
        return reply


class CountingRetriever(FakeRetriever):
    """Counts searches, so a test can show that a turn never reached the store."""

    def __init__(self) -> None:
        super().__init__()
        self.queries = 0

    def query(
        self, scope: str, query_vector: list[float], k: int
    ) -> list[RetrievedChunk]:
        self.queries += 1
        return super().query(scope, query_vector, k)


class FakeDocuments:
    """The kept text, in a dict, keyed by field and upload as the real store is.
    `writes` is what lets a test say a document was kept once, or not at all."""

    def __init__(self) -> None:
        self._kept: dict[tuple[str, str], str] = {}
        self.writes = 0

    def keep(self, scope: str, upload: str, filename: str, text: str) -> None:
        self._kept[(scope, upload)] = text
        self.writes += 1

    def read(self, scope: str, upload: str) -> str | None:
        return self._kept.get((scope, upload))

    def forget(self, scope: str) -> None:
        """Every file of one field gone, as a directory emptied behind cora's back."""
        self._kept = {key: text for key, text in self._kept.items() if key[0] != scope}


class KeepsNothingDocuments(FakeDocuments):
    """A store that accepts and forgets: what an index written before cora kept any
    document text looks like from the outside."""

    def keep(self, scope: str, upload: str, filename: str, text: str) -> None:
        return None


class FailingDocuments(FakeDocuments):
    def read(self, scope: str, upload: str) -> str | None:
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
        self,
        scope: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
        file_hash: str,
    ) -> None:
        raise self.error

    def query(
        self, scope: str, query_vector: list[float], k: int
    ) -> list[RetrievedChunk]:
        raise self.error

    def sources(self, scope: str) -> list[str]:
        raise self.error

    def contains(self, scope: str, file_hash: str) -> bool:
        raise self.error


@dataclass
class FailingChatModel:
    error: Exception

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
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


class FakeConversations:
    """Turns per thread, in the order they were recorded. `sessions` is newest first by
    the thread that last spoke, which is the order the real store promises."""

    def __init__(self) -> None:
        self._recorded: dict[str, list[Turn]] = {}
        self._spoke: list[str] = []

    def record(self, thread_id: str, turn: Turn) -> None:
        self._recorded.setdefault(thread_id, []).append(turn)
        if thread_id in self._spoke:
            self._spoke.remove(thread_id)
        self._spoke.append(thread_id)

    def turns(self, thread_id: str) -> tuple[Turn, ...]:
        return tuple(self._recorded.get(thread_id, ()))

    def sessions(self) -> tuple[Session, ...]:
        return tuple(
            Session(thread_id=thread, opened_with=self._recorded[thread][0].question)
            for thread in reversed(self._spoke)
        )


@dataclass
class FailingConversations:
    """A store that went away mid-session: every write refuses."""

    error: Exception = field(default_factory=ConversationStoreError)

    def record(self, thread_id: str, turn: Turn) -> None:
        raise self.error

    def turns(self, thread_id: str) -> tuple[Turn, ...]:
        raise self.error

    def sessions(self) -> tuple[Session, ...]:
        raise self.error


@dataclass
class UnopenableSessions:
    """Lists its conversations and refuses to read one: the store that went away between
    the page being drawn and a session on it being clicked."""

    listing: Any
    error: Exception = field(default_factory=ConversationStoreError)

    def record(self, thread_id: str, turn: Turn) -> None:
        self.listing.record(thread_id, turn)

    def turns(self, thread_id: str) -> tuple[Turn, ...]:
        raise self.error

    def sessions(self) -> tuple[Session, ...]:
        return self.listing.sessions()


def host_for(
    module: str = "fixture_plugins.valid",
    *,
    documents: ContextSource | None = None,
    model: ChatModel | None = None,
    memory: Memory | None = None,
    settings: dict[str, str] | None = None,
) -> PluginHost:
    """A host a test can hand a plugin, with fakes behind cora's own parts.

    The real host rather than a stand-in for it: what a plugin registers, and what it
    is refused for registering, are the host's own rules.
    """
    return PluginHost(
        module=module,
        index=documents or FakeContextSource(),
        model=model or ScriptedChatModel([ModelReply(text="ok")]),
        memory=memory,
        settings=settings or {},
    )
