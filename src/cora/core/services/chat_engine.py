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
    return Message(role="tool", content=result.render(), tool_call_id=result.call_id)


def _unique_sources(chunks: list[RetrievedChunk]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(hit.chunk.source for hit in chunks))


def cited_numbers(text: str) -> tuple[int, ...]:
    runs = re.findall(r"(?<![\w\]])(?:\[\d+\])+", text)
    found = (int(number) for run in runs for number in re.findall(r"\d+", run))
    return tuple(dict.fromkeys(found))


@dataclass(frozen=True)
class Source:
    number: int
    name: str


@dataclass(frozen=True)
class Context:
    text: str
    sources: tuple[Source, ...]


def build_context_block(chunks: list[RetrievedChunk]) -> Context:
    names = _unique_sources(chunks)
    sources = tuple(Source(number, name) for number, name in enumerate(names, start=1))
    number_of = {source.name: source.number for source in sources}
    body = "\n".join(
        f"[{number_of[hit.chunk.source]}] {hit.chunk.source}: {hit.chunk.text}"
        for hit in chunks
    )
    citation_rule = "Cite sources by their bracketed number, e.g. [1]."
    return Context(text=f"{body}\n\n{citation_rule}", sources=sources)


def _cited_sources(text: str, sources: tuple[Source, ...]) -> tuple[Source, ...]:
    by_number = {source.number: source for source in sources}
    cited = (by_number[n] for n in cited_numbers(text) if n in by_number)
    return tuple(sorted(cited, key=lambda source: source.number))


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: tuple[Source, ...] = ()
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
    build_context: Callable[[list[RetrievedChunk]], Context] = build_context_block

    def answer(self, user_input: str, history: tuple[Turn, ...] = ()) -> ChatResult:
        validated = self.validation.validate(user_input)
        chunks = self.knowledge_base.search(validated, self.top_k)
        context = self.build_context(chunks)
        messages = self._initial_messages(validated, context, history)
        text, tool_results = self._run_tool_loop(messages)
        return ChatResult(
            answer=text,
            sources=_cited_sources(text, context.sources),
            tool_results=tool_results,
        )

    def _initial_messages(
        self,
        user_input: str,
        context: Context,
        history: tuple[Turn, ...],
    ) -> list[Message]:
        system = Message(
            role="system",
            content=f"{self.system_prompt}\n\n{context.text}",
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
