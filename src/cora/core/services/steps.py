from dataclasses import dataclass
from typing import Protocol

from cora.core.agent_state import AgentState
from cora.core.citations import Citable, Source
from cora.core.ports.chat_model import ChatModel, Message
from cora.core.ports.plugin import Tool, ToolCall, ToolResult


class ToolExecutor(Protocol):
    def execute(self, call: ToolCall) -> ToolResult: ...


@dataclass(frozen=True)
class ModelStep:
    chat_model: ChatModel
    tools: tuple[Tool, ...]

    def __call__(self, state: AgentState) -> AgentState:
        reply = self.chat_model.complete(tuple(state.get("messages", ())), self.tools)
        appended = Message(
            role="assistant", content=reply.text, tool_calls=reply.tool_calls
        )
        partial: AgentState = {"messages": [appended], "rounds": 1}
        if reply.is_final:
            partial["answer"] = reply.text
        return partial


@dataclass(frozen=True)
class ToolStep:
    tool_runtime: ToolExecutor

    def __call__(self, state: AgentState) -> AgentState:
        known = tuple(state.get("sources", ()))
        results: list[ToolResult] = []
        added: list[Source] = []
        for call in _requested_calls(state):
            result, registered = _register(
                self.tool_runtime.execute(call), known + tuple(added)
            )
            results.append(result)
            added.extend(registered)
        return {
            "messages": [_tool_message(result) for result in results],
            "tool_results": results,
            "sources": added,
        }


def _requested_calls(state: AgentState) -> tuple[ToolCall, ...]:
    messages = state.get("messages") or []
    return messages[-1].tool_calls if messages else ()


def _register(
    result: ToolResult, known: tuple[Source, ...]
) -> tuple[ToolResult, tuple[Source, ...]]:
    if not isinstance(result.payload, Citable):
        return result, ()
    context = result.payload.register(known)
    return ToolResult(call_id=result.call_id, payload=context.text), context.sources


def _tool_message(result: ToolResult) -> Message:
    return Message(role="tool", content=result.render(), tool_call_id=result.call_id)
