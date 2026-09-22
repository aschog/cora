import hashlib
import math
from dataclasses import dataclass, field, replace
from typing import NamedTuple

from cora.domain.chunk import Chunk
from cora.domain.conversation import Conversation, Turn
from cora.domain.errors import (
    ConversationStoreError,
    FileNameRejectedError,
    FileTooLargeToKeepError,
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
from cora.ports.context_source import ContextSource, Document
from cora.ports.files import MOST_BYTES, Files, plain_name
from cora.ports.loading import Loaders
from cora.ports.memory import Fact, Memory
from cora.ports.output import Output
from cora.ports.plugin import Tool
from cora.ports.retrieval import RetrievedChunk
from cora.ports.store import Store


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
    def __init__(self) -> None:
        self._records: list[_Record] = []

    def add(
        self,
        scope: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
        file_hash: str,
    ) -> None:
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

    def forget(self, scope: str, file_hash: str) -> None:
        self._records = [
            r
            for r in self._records
            if not (r.scope == scope and r.file_hash == file_hash)
        ]

    def uploads(self, scope: str, source: str) -> list[str]:
        return list(
            dict.fromkeys(
                r.file_hash
                for r in self._records
                if r.scope == scope and r.chunk.source == source
            )
        )

    def contains(self, scope: str, file_hash: str) -> bool:
        return any(r.file_hash == file_hash and r.scope == scope for r in self._records)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


class ScriptedChatModel:
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
    def __init__(self) -> None:
        super().__init__()
        self.queries = 0

    def query(
        self, scope: str, query_vector: list[float], k: int
    ) -> list[RetrievedChunk]:
        self.queries += 1
        return super().query(scope, query_vector, k)


class FakeDocuments:
    def __init__(self) -> None:
        self._kept: dict[tuple[str, str], str] = {}
        self.writes = 0

    def keep(self, scope: str, upload: str, filename: str, text: str) -> None:
        self._kept[(scope, upload)] = text
        self.writes += 1

    def read(self, scope: str, upload: str) -> str | None:
        return self._kept.get((scope, upload))

    def forget(self, scope: str, upload: str) -> None:
        self._kept.pop((scope, upload), None)

    def emptied(self, scope: str) -> None:
        self._kept = {key: text for key, text in self._kept.items() if key[0] != scope}


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
    held: list[Document] = field(default_factory=list)
    last_query: str | None = None
    last_k: int | None = None

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        self.last_query = query
        self.last_k = k
        return self.results

    def all(self) -> list[Document]:
        return self.held


def _decode(data: bytes, filename: str) -> str:
    return data.decode("utf-8")


TEXT_LOADERS: Loaders = {".txt": _decode, ".md": _decode}


class FakeConversations:
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

    def forget(self, thread_id: str) -> None:
        self._recorded.pop(thread_id, None)
        if thread_id in self._spoke:
            self._spoke.remove(thread_id)

    def opened(self) -> tuple[Conversation, ...]:
        return tuple(
            Conversation(
                thread_id=thread, opened_with=self._recorded[thread][0].question
            )
            for thread in reversed(self._spoke)
        )


@dataclass
class FailingConversations:
    error: Exception = field(default_factory=ConversationStoreError)

    def record(self, thread_id: str, turn: Turn) -> None:
        raise self.error

    def turns(self, thread_id: str) -> tuple[Turn, ...]:
        raise self.error

    def forget(self, thread_id: str) -> None:
        raise self.error

    def opened(self) -> tuple[Conversation, ...]:
        raise self.error


@dataclass
class FakeOutput:
    root: str = "/kept"
    written: dict[str, str] = field(default_factory=dict)

    def write(self, name: str, text: str) -> str:
        self.written[name] = text
        return f"{self.root}/{name}"


@dataclass
class FakeStore:
    kept: dict[tuple[str, str], str] = field(default_factory=dict)

    def read(self, plugin: str, name: str) -> str | None:
        return self.kept.get((plugin, name))

    def keep(self, plugin: str, name: str, value: str | None) -> None:
        if value is None:
            self.kept.pop((plugin, name), None)
            return
        self.kept[(plugin, name)] = value

    def forget(self, plugin: str) -> None:
        for held, name in list(self.kept):
            if held == plugin:
                del self.kept[(held, name)]


@dataclass
class FakeFiles:
    kept: dict[tuple[str, str], str] = field(default_factory=dict)
    cap: int = MOST_BYTES

    def names(self, scope: str) -> tuple[str, ...]:
        return tuple(sorted(name for held, name in self.kept if held == scope))

    def read(self, scope: str, name: str) -> str | None:
        return self.kept.get((_plain(scope), _plain(name)))

    def write(self, scope: str, name: str, text: str | None) -> None:
        held = (_plain(scope), _plain(name))
        if text is None:
            self.kept.pop(held, None)
            return
        if len(text.encode("utf-8")) > self.cap:
            raise FileTooLargeToKeepError(self.cap)
        self.kept[held] = text


def _plain(name: str) -> str:
    if not plain_name(name):
        raise FileNameRejectedError(name)
    return name


def host_for(
    module: str = "fixture_plugins.valid",
    *,
    documents: ContextSource | None = None,
    model: ChatModel | None = None,
    memory: Memory | None = None,
    output: Output | None = None,
    store: Store | None = None,
    files: Files | None = None,
    settings: dict[str, str] | None = None,
) -> PluginHost:
    return PluginHost(
        module=module,
        index=documents or FakeContextSource(),
        model=model or ScriptedChatModel([ModelReply(text="ok")]),
        memory=memory,
        output=output,
        kept=store,
        kept_files=files,
        settings=settings or {},
    )
