import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from cora.core.errors import ToolLoopLimitError
from cora.core.ports.chat_model import ChatModel, Message
from cora.core.ports.plugin import Tool, ToolCall, ToolResult
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.turn import Turn


class ContextSource(Protocol):
    def search(self, query: str, k: int) -> list[RetrievedChunk]: ...


class InputValidator(Protocol):
    def validate(self, user_input: str) -> str: ...


class ToolExecutor(Protocol):
    def execute(self, call: ToolCall) -> ToolResult: ...


def _tool_message(result: ToolResult) -> Message:
    if result.error is not None:
        content = result.error
    elif isinstance(result.payload, str):
        content = result.payload
    else:
        content = json.dumps(result.payload, default=str)
    return Message(role="tool", content=content, tool_call_id=result.call_id)


def _unique_sources(chunks: list[RetrievedChunk]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(hit.chunk.source for hit in chunks))


def cited_numbers(text: str) -> tuple[int, ...]:
    found = (int(match) for match in re.findall(r"\[(\d+)\]", text))
    return tuple(dict.fromkeys(found))


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
    validation: InputValidator
    tool_runtime: ToolExecutor
    top_k: int
    max_tool_rounds: int
    system_prompt: str
    max_history_turns: int
    tools: tuple[Tool, ...] = ()
    build_context: Callable[[list[RetrievedChunk]], str] = build_context_block

    def answer(self, user_input: str, history: tuple[Turn, ...] = ()) -> ChatResult:
        validated = self.validation.validate(user_input)
        chunks = self.knowledge_base.search(validated, self.top_k)
        messages = self._initial_messages(validated, chunks, history)
        text, tool_results = self._run_tool_loop(messages)
        return ChatResult(
            answer=text, sources=_unique_sources(chunks), tool_results=tool_results
        )

    def _initial_messages(
        self,
        user_input: str,
        chunks: list[RetrievedChunk],
        history: tuple[Turn, ...],
    ) -> list[Message]:
        system = Message(
            role="system",
            content=f"{self.system_prompt}\n\n{self.build_context(chunks)}",
        )
        recent = history[max(len(history) - self.max_history_turns, 0) :]
        past = [Message(role=turn.role, content=turn.text) for turn in recent]
        return [system, *past, Message(role="user", content=user_input)]

    def _run_tool_loop(
        self, messages: list[Message]
    ) -> tuple[str, tuple[ToolResult, ...]]:
        tool_results: list[ToolResult] = []
        for _ in range(self.max_tool_rounds):
            reply = self.chat_model.complete(tuple(messages), self.tools)
            if reply.is_final:
                return reply.text, tuple(tool_results)
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
