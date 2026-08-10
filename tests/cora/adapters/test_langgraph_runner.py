import pytest

from cora.adapters.langgraph_runner import (
    LangGraphRunner,
    Step,
    recursion_limit_for,
)
from cora.core.agent_state import AgentState
from cora.core.citations import Source
from cora.core.errors import InputRejectedError, LlmError, ToolLoopLimitError
from cora.core.ports.chat_model import ChatModel, Message, ModelReply, Role
from cora.core.ports.plugin import Tool, ToolCall, ToolResult
from cora.core.services.steps import ModelStep, PrepareStep, Router, ToolStep
from cora.core.services.tool_runtime import ToolRuntime
from cora.core.services.validation import EmptyInputRule, ValidationPipeline
from fakes import FailingChatModel, add_tool

ROUNDS = 8


def _said(role: Role, content: str) -> list[Message]:
    return [Message(role=role, content=content)]


def _prepare(state: AgentState) -> AgentState:
    return {"messages": _said("user", state["question"])}


def _ran(state: AgentState) -> AgentState:
    return {"messages": _said("tool", "ran")}


def _runner(
    *,
    prepare: Step = _prepare,
    model: Step,
    tools: Step = _ran,
    rounds: int = ROUNDS,
    recursion_limit: int | None = None,
) -> LangGraphRunner:
    return LangGraphRunner(
        prepare=prepare,
        model=model,
        tools=tools,
        router=Router(max_tool_rounds=rounds),
        recursion_limit=recursion_limit or recursion_limit_for(rounds),
    )


def test_run_walks_prepare_then_model_then_tools_then_model() -> None:
    visited: list[str] = []

    def prepare(state: AgentState) -> AgentState:
        visited.append("prepare")
        return _prepare(state)

    def model(state: AgentState) -> AgentState:
        visited.append("model")
        if state.get("rounds"):
            return {"messages": _said("assistant", "done"), "rounds": 1, "answer": "d"}
        return {"messages": _said("assistant", "asking"), "rounds": 1}

    def tools(state: AgentState) -> AgentState:
        visited.append("tools")
        return {"messages": _said("tool", "ran")}

    final = _runner(prepare=prepare, model=model, tools=tools).run({"question": "q"})

    assert visited == ["prepare", "model", "tools", "model"]
    assert final["answer"] == "d"


def test_the_returned_state_accumulated_every_partial() -> None:
    def model(state: AgentState) -> AgentState:
        if state.get("rounds"):
            return {"messages": _said("assistant", "done"), "rounds": 1, "answer": "d"}
        return {"messages": _said("assistant", "asking"), "rounds": 1}

    def tools(state: AgentState) -> AgentState:
        return {
            "messages": _said("tool", "ran"),
            "tool_results": [ToolResult(call_id="c1", payload="passages")],
            "sources": [Source(1, "note.md")],
        }

    final = _runner(model=model, tools=tools).run({"question": "q"})

    assert [m.content for m in final["messages"]] == ["q", "asking", "ran", "done"]
    assert final["tool_results"] == [ToolResult(call_id="c1", payload="passages")]
    assert final["sources"] == [Source(1, "note.md")]
    assert final["rounds"] == 2


def test_a_runaway_graph_surfaces_as_the_friendly_give_up() -> None:
    def endless(state: AgentState) -> AgentState:
        return {"messages": _said("assistant", "again"), "rounds": 1}

    runner = _runner(model=endless, rounds=999, recursion_limit=4)

    with pytest.raises(ToolLoopLimitError):
        runner.run({"question": "q"})


class _AlwaysCalling:
    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.completions += 1
        return ModelReply(
            tool_calls=(
                ToolCall(
                    name="add",
                    arguments={"a": 1, "b": 2},
                    call_id=f"c{self.completions}",
                ),
            )
        )


def _real_runner(model: ChatModel, rounds: int) -> LangGraphRunner:
    return LangGraphRunner(
        prepare=PrepareStep(
            validation=ValidationPipeline((EmptyInputRule(),), ()),
            system_prompt="SYS",
            max_history_turns=20,
        ),
        model=ModelStep(chat_model=model, tools=(add_tool(),)),
        tools=ToolStep(ToolRuntime(tools=(add_tool(),))),
        router=Router(max_tool_rounds=rounds),
        recursion_limit=recursion_limit_for(rounds),
    )


def test_the_round_budget_fires_before_the_graphs_own_limit() -> None:
    model = _AlwaysCalling()

    with pytest.raises(ToolLoopLimitError):
        _real_runner(model, rounds=3).run({"question": "loop forever"})

    assert model.completions == 3


def test_an_input_rejection_from_prepare_travels_out_unwrapped() -> None:
    with pytest.raises(InputRejectedError):
        _real_runner(_AlwaysCalling(), rounds=3).run({"question": "   "})


def test_an_adapter_error_from_a_step_travels_out_unwrapped() -> None:
    error = LlmError()

    with pytest.raises(LlmError) as exc_info:
        _real_runner(FailingChatModel(error), rounds=3).run({"question": "hi"})

    assert exc_info.value is error
