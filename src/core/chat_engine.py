from dataclasses import dataclass
from typing import Protocol

from core.chat_model import ChatModel, Message
from core.plugin import ToolResult
from core.retrieval import RetrievedChunk


class ContextSource(Protocol):
    def search(self, query: str, k: int) -> list[RetrievedChunk]: ...


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: tuple[str, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()


@dataclass(frozen=True)
class ChatEngine:
    chat_model: ChatModel
    knowledge_base: ContextSource
    top_k: int

    def answer(self, user_input: str) -> ChatResult:
        chunks = self.knowledge_base.search(user_input, self.top_k)
        sources = tuple(dict.fromkeys(hit.chunk.source for hit in chunks))
        messages = (Message(role="user", content=user_input),)
        reply = self.chat_model.complete(messages, ())
        return ChatResult(answer=reply.text, sources=sources)
