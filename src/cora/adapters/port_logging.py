import logging
from dataclasses import dataclass

from cora.core.chunk import Chunk
from cora.core.ports.chat_model import ChatModel, Message, ModelReply
from cora.core.ports.embedding import Embedder
from cora.core.ports.plugin import Tool
from cora.core.ports.retrieval import RetrievedChunk, Retriever

MAX_LOGGED_CHARS = 120

log = logging.getLogger(__name__)


def truncate(text: str) -> str:
    if len(text) <= MAX_LOGGED_CHARS:
        return text
    return text[: MAX_LOGGED_CHARS - 1] + "…"


@dataclass(frozen=True)
class LoggingChatModel:
    inner: ChatModel

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        log.debug(
            "chat request: %d messages [%s], last: %s",
            len(messages),
            truncate(", ".join(message.role for message in messages)),
            truncate(messages[-1].content) if messages else "",
        )
        reply = self.inner.complete(messages, tools)
        log.debug(
            "chat reply: tool calls [%s], text: %s",
            ", ".join(call.name for call in reply.tool_calls),
            truncate(reply.text),
        )
        return reply


@dataclass(frozen=True)
class LoggingRetriever:
    inner: Retriever

    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None:
        log.debug(
            "indexed: %d chunks from %s",
            len(chunks),
            truncate(chunks[0].source) if chunks else "an empty batch",
        )
        self.inner.add(chunks, vectors, file_hash)

    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]:
        hits = self.inner.query(query_vector, k)
        log.debug(
            "retrieval: k=%d, %d hits [%s]",
            k,
            len(hits),
            truncate(", ".join(_describe(hit) for hit in hits)),
        )
        return hits

    def sources(self) -> list[str]:
        return self.inner.sources()

    def contains(self, file_hash: str) -> bool:
        return self.inner.contains(file_hash)


@dataclass(frozen=True)
class LoggingEmbedder:
    inner: Embedder

    def embed(self, texts: list[str]) -> list[list[float]]:
        log.debug("embedded: %d texts", len(texts))
        return self.inner.embed(texts)


def _describe(hit: RetrievedChunk) -> str:
    return f"{hit.chunk.source}#{hit.chunk.index} {hit.score:.2f}"
