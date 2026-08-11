import pytest

from cora.adapters.langgraph_runner import (
    LangGraphRunner,
    Step,
    recursion_limit_for,
)
from cora.core.service_layer.steps import (
    GroundStep,
    ModelStep,
    PrepareStep,
    Router,
    ToolStep,
)
from cora.core.service_layer.tool_runtime import ToolRuntime
from cora.core.service_layer.validation import EmptyInputRule, ValidationPipeline
from cora.domain.agent_state import AgentState
from cora.domain.citations import Source
from cora.domain.errors import InputRejectedError, LlmError, ToolLoopLimitError
from cora.domain.trace import ToolUse
from cora.ports.chat_model import ChatModel, Message, ModelReply, Role
from cora.ports.plugin import Tool, ToolCall
from fakes import FailingChatModel, FakeContextSource, add_tool

ROUNDS = 8


def _final(runner: LangGraphRunner, state: AgentState) -> AgentState:
    return list(runner.run(state))[-1]


def _said(role: Role, content: str) -> list[Message]:
    return [Message(role=role, content=content)]


def _asked_for_a_tool(content: str) -> list[Message]:
    """A reply the router reads as unfinished: it is asking for a tool."""
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")
    return [Message(role="assistant", content=content, tool_calls=(call,))]


def _prepare(state: AgentState) -> AgentState:
    return {"messages": _said("user", state["question"])}


def _ran(state: AgentState) -> AgentState:
    return {"messages": _said("tool", "ran")}


def _nudge(state: AgentState) -> AgentState:
    return {"messages": _said("system", "search first"), "answer_in_hand": "off"}


def _runner(
    *,
    prepare: Step = _prepare,
    model: Step,
    tools: Step = _ran,
    ground: Step = _nudge,
    grounded: bool = False,
    rounds: int = ROUNDS,
    recursion_limit: int | None = None,
) -> LangGraphRunner:
    return LangGraphRunner(
        prepare=prepare,
        model=model,
        tools=tools,
        ground=ground,
        router=Router(max_tool_rounds=rounds, grounded=grounded),
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
        return {"messages": _asked_for_a_tool("asking"), "rounds": 1}

    def tools(state: AgentState) -> AgentState:
        visited.append("tools")
        return {"messages": _said("tool", "ran")}

    final = _final(
        _runner(prepare=prepare, model=model, tools=tools), {"question": "q"}
    )

    assert visited == ["prepare", "model", "tools", "model"]
    assert final["answer"] == "d"


def test_the_returned_state_accumulated_every_partial() -> None:
    def model(state: AgentState) -> AgentState:
        if state.get("rounds"):
            return {"messages": _said("assistant", "done"), "rounds": 1, "answer": "d"}
        return {"messages": _asked_for_a_tool("asking"), "rounds": 1}

    def tools(state: AgentState) -> AgentState:
        return {
            "messages": _said("tool", "ran"),
            "trace": [ToolUse(name="search_documents", outcome="1 passage")],
            "sources": [Source(1, "note.md")],
        }

    final = _final(_runner(model=model, tools=tools), {"question": "q"})

    assert [m.content for m in final["messages"]] == ["q", "asking", "ran", "done"]
    assert final["trace"] == [ToolUse(name="search_documents", outcome="1 passage")]
    assert final["sources"] == [Source(1, "note.md")]
    assert final["rounds"] == 2


def test_an_ungrounded_answer_goes_back_through_the_model() -> None:
    visited: list[str] = []

    def model(state: AgentState) -> AgentState:
        visited.append("model")
        if "answer_in_hand" in state:
            return {"messages": _said("assistant", "grounded"), "answer": "grounded"}
        return {"messages": _said("assistant", "off the cuff"), "answer": "off"}

    def ground(state: AgentState) -> AgentState:
        visited.append("ground")
        return {"messages": _said("system", "search first"), "answer_in_hand": "off"}

    final = _final(
        _runner(model=model, ground=ground, grounded=True), {"question": "q"}
    )

    assert visited == ["model", "ground", "model"]
    assert final["answer"] == "grounded"


def test_a_step_is_seen_before_the_run_is_over() -> None:
    """Pull states until the first round's work shows up: the second round must
    not have run yet, or the caller is being handed a finished run."""
    completions: list[str] = []

    def model(state: AgentState) -> AgentState:
        completions.append(f"round {len(completions) + 1}")
        if state.get("rounds"):
            return {"messages": _said("assistant", "done"), "rounds": 1}
        return {"messages": _asked_for_a_tool("asking"), "rounds": 1}

    states = _runner(model=model).run({"question": "q"})
    for state in states:
        if state.get("rounds"):
            break

    assert completions == ["round 1"]


def test_a_runaway_graph_surfaces_as_the_friendly_give_up() -> None:
    def endless(state: AgentState) -> AgentState:
        return {"messages": _asked_for_a_tool("again"), "rounds": 1}

    runner = _runner(model=endless, rounds=999, recursion_limit=4)

    with pytest.raises(ToolLoopLimitError):
        _final(runner, {"question": "q"})


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


def _real_runner(
    model: ChatModel, rounds: int, grounded: bool = False
) -> LangGraphRunner:
    return LangGraphRunner(
        ground=GroundStep(
            reminder="weigh these", context_source=FakeContextSource(), top_k=3
        ),
        prepare=PrepareStep(
            validation=ValidationPipeline((EmptyInputRule(),), ()),
            system_prompt="SYS",
            max_history_turns=20,
        ),
        model=ModelStep(chat_model=model, tools=(add_tool(),)),
        tools=ToolStep(ToolRuntime(tools=(add_tool(),))),
        router=Router(max_tool_rounds=rounds, grounded=grounded),
        recursion_limit=recursion_limit_for(rounds),
    )


@pytest.mark.parametrize("rounds", [1, 2, 3, 8, 12])
def test_the_round_budget_fires_before_the_graphs_own_limit(rounds: int) -> None:
    """Across the budgets a deployment can actually be set to, including the
    default: the graph's limit must never be what cuts a run short."""
    model = _AlwaysCalling()

    with pytest.raises(ToolLoopLimitError) as exc_info:
        _final(_real_runner(model, rounds=rounds), {"question": "loop forever"})

    assert model.completions == rounds
    assert exc_info.value.__cause__ is None


def test_the_round_budget_still_fires_first_when_the_gate_has_added_a_round() -> None:
    """`run` turns a `GraphRecursionError` into the same `ToolLoopLimitError`, so
    the count is what tells the two apart: the budget tripping means every round
    was spent, the graph tripping means it was cut short."""

    class _AnswersThenLoops:
        def __init__(self) -> None:
            self.completions = 0

        def complete(
            self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
        ) -> ModelReply:
            self.completions += 1
            if self.completions == 1:
                return ModelReply(text="off the cuff")
            return ModelReply(
                tool_calls=(
                    ToolCall(
                        name="add",
                        arguments={"a": 1, "b": 2},
                        call_id=f"c{self.completions}",
                    ),
                )
            )

    model = _AnswersThenLoops()

    with pytest.raises(ToolLoopLimitError) as exc_info:
        _final(_real_runner(model, rounds=3, grounded=True), {"question": "q"})

    assert model.completions == 3
    assert exc_info.value.__cause__ is None


def test_an_input_rejection_from_prepare_travels_out_unwrapped() -> None:
    with pytest.raises(InputRejectedError):
        _final(_real_runner(_AlwaysCalling(), rounds=3), {"question": "   "})


def test_an_adapter_error_from_a_step_travels_out_unwrapped() -> None:
    error = LlmError()

    with pytest.raises(LlmError) as exc_info:
        _final(_real_runner(FailingChatModel(error), rounds=3), {"question": "hi"})

    assert exc_info.value is error
