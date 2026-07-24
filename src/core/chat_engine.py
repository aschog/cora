from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from core.chat_model import ChatModel, Message
from core.errors import ToolLoopLimitError
from core.plugin import Tool, ToolCall, ToolResult
from core.retrieval import RetrievedChunk


class ContextSource(Protocol):
    def search(self, query: str, k: int) -> list[RetrievedChunk]: ...


class ToolExecutor(Protocol):
    def execute(self, call: ToolCall) -> ToolResult: ...


def _tool_message(result: ToolResult) -> Message:
    content = result.error if result.error is not None else str(result.payload)
    return Message(role="tool", content=content, tool_call_id=result.call_id)


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    context = "\n".join(
        f"[{number}] {hit.chunk.source}: {hit.chunk.text}"
        for number, hit in enumerate(chunks, start=1)
    )
    citation_rule = "Cite sources by their bracketed number, e.g. [1]."
    return f"{context}\n\n{citation_rule}"


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: tuple[str, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()


@dataclass(frozen=True)
class ChatEngine:
    chat_model: ChatModel
    knowledge_base: ContextSource
    tool_runtime: ToolExecutor
    top_k: int
    max_tool_rounds: int
    system_prompt: str
    tools: tuple[Tool, ...] = ()
    build_context: Callable[[list[RetrievedChunk]], str] = build_context_block

    def answer(self, user_input: str) -> ChatResult:
        chunks = self.knowledge_base.search(user_input, self.top_k)
        sources = tuple(dict.fromkeys(hit.chunk.source for hit in chunks))
        messages: list[Message] = [
            Message(
                role="system",
                content=f"{self.system_prompt}\n\n{self.build_context(chunks)}",
            ),
            Message(role="user", content=user_input),
        ]
        tool_results: list[ToolResult] = []
        for _ in range(self.max_tool_rounds):
            reply = self.chat_model.complete(tuple(messages), self.tools)
            if reply.is_final:
                return ChatResult(
                    answer=reply.text,
                    sources=sources,
                    tool_results=tuple(tool_results),
                )
            messages.append(
                Message(
                    role="assistant", content=reply.text, tool_calls=reply.tool_calls
                )
            )
            for call in reply.tool_calls:
                result = self.tool_runtime.execute(call)
                tool_results.append(result)
                messages.append(_tool_message(result))
        raise ToolLoopLimitError
