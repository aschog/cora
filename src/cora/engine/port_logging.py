import logging
from dataclasses import dataclass

from cora.domain.chunk import Chunk
from cora.domain.metadata_filter import MetadataFilter
from cora.ports.chat_model import ChatModel, Message, ModelReply
from cora.ports.embedding import Embedder
from cora.ports.plugin import Tool
from cora.ports.retrieval import RetrievedChunk, Retriever

MAX_LOGGED_CHARS = 120

log = logging.getLogger(__name__)


def truncate(text: str) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= MAX_LOGGED_CHARS:
        return one_line
    return one_line[: MAX_LOGGED_CHARS - 1] + "…"


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
            truncate(", ".join(call.name for call in reply.tool_calls)),
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
            "indexing: %d chunks from %s",
            len(chunks),
            truncate(chunks[0].source) if chunks else "an empty batch",
        )
        self.inner.add(chunks, vectors, file_hash)

    def query(
        self,
        query_vector: list[float],
        k: int,
        metadata_filter: MetadataFilter | None = None,
    ) -> list[RetrievedChunk]:
        hits = self.inner.query(query_vector, k, metadata_filter)
        log.debug(
            "retrieval: k=%d, filter=%s, %d hits [%s]",
            k,
            _describe_filter(metadata_filter),
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
        log.debug("embedding: %d texts", len(texts))
        return self.inner.embed(texts)


def _describe(hit: RetrievedChunk) -> str:
    return f"{hit.chunk.source}#{hit.chunk.index} {hit.score:.2f}"


def _describe_filter(metadata_filter: MetadataFilter | None) -> str:
    if metadata_filter is None:
        return "none"
    return f"{metadata_filter.field}={metadata_filter.value}"
