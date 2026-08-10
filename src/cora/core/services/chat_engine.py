from collections.abc import Callable
from dataclasses import dataclass

from cora.core.citations import Context, build_context_block, cited_sources
from cora.core.context_source import ContextSource
from cora.core.errors import ToolLoopLimitError
from cora.core.ports.chat_model import ChatModel, Message
from cora.core.ports.plugin import Tool, ToolResult
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.services.agent import ChatResult
from cora.core.services.steps import InputValidator, ToolExecutor
from cora.core.turn import Turn


def _tool_message(result: ToolResult) -> Message:
    return Message(role="tool", content=result.render(), tool_call_id=result.call_id)


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
            sources=cited_sources(text, context.sources),
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
