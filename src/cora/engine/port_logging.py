"""The three outward ports, wrapped so `CORA_DEBUG` can watch them.

Each wrapper implements the port it wraps and adds nothing to it: what is logged is what
crossed the seam, and nothing about a turn changes because someone is watching.
"""

import logging
from dataclasses import dataclass

from cora.domain.chunk import Chunk
from cora.ports.chat_model import ChatModel, Message, ModelReply, TextSink, unheard
from cora.ports.embedding import Embedder
from cora.ports.plugin import Tool
from cora.ports.retrieval import RetrievedChunk, Retriever

MAX_LOGGED_CHARS = 120

log = logging.getLogger(__name__)


def truncate(text: str) -> str:
    """One line, at most `MAX_LOGGED_CHARS` of it, ending in an ellipsis when cut.

    A prompt or a passage would otherwise put a page of text through the log for every
    turn, which is how a debug log stops being read.
    """
    one_line = " ".join(text.split())
    if len(one_line) <= MAX_LOGGED_CHARS:
        return one_line
    return one_line[: MAX_LOGGED_CHARS - 1] + "…"


@dataclass(frozen=True)
class LoggingChatModel:
    """A `ChatModel` that logs what was asked and what came back."""

    inner: ChatModel

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        """The reply, unchanged. Logged around the call, so a failure shows as one."""
        log.debug(
            "chat request: %d messages [%s], last: %s",
            len(messages),
            truncate(", ".join(message.role for message in messages)),
            truncate(messages[-1].content) if messages else "",
        )
        reply = self.inner.complete(messages, tools, on_text)
        log.debug(
            "chat reply: tool calls [%s], text: %s",
            truncate(", ".join(call.name for call in reply.tool_calls)),
            truncate(reply.text),
        )
        return reply


@dataclass(frozen=True)
class LoggingRetriever:
    """A `Retriever` that logs what went into the index and what came out of it."""

    inner: Retriever

    def add(
        self,
        scope: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
        file_hash: str,
    ) -> None:
        """Index the chunks, saying how many, from where and into which field."""
        log.debug(
            "indexing: %d chunks from %s into %s",
            len(chunks),
            truncate(chunks[0].source) if chunks else "an empty batch",
            scope,
        )
        self.inner.add(scope, chunks, vectors, file_hash)

    def query(
        self, scope: str, query_vector: list[float], k: int
    ) -> list[RetrievedChunk]:
        """The hits, unchanged, with the field, their sources and scores in the log."""
        hits = self.inner.query(scope, query_vector, k)
        log.debug(
            "retrieval: scope=%s, k=%d, %d hits [%s]",
            scope,
            k,
            len(hits),
            truncate(", ".join(_describe(hit) for hit in hits)),
        )
        return hits

    def sources(self, scope: str) -> list[str]:
        """Straight through: a list of filenames says nothing a log needs."""
        return self.inner.sources(scope)

    def contains(self, scope: str, file_hash: str) -> bool:
        """Straight through."""
        return self.inner.contains(scope, file_hash)


@dataclass(frozen=True)
class LoggingEmbedder:
    """An `Embedder` that logs how much was embedded, never the text itself."""

    inner: Embedder

    def embed(self, texts: list[str]) -> list[list[float]]:
        """The vectors, unchanged."""
        log.debug("embedding: %d texts", len(texts))
        return self.inner.embed(texts)


def _describe(hit: RetrievedChunk) -> str:
    return f"{hit.chunk.source}#{hit.chunk.index} {hit.score:.2f}"
