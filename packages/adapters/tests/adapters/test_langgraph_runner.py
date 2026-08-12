import pytest

from cora.adapters.langgraph_runner import (
    LangGraphRunner,
    Step,
    _trace_kinds,
    checkpointed_types,
    recursion_limit_for,
)
from cora.domain.agent_state import AgentState
from cora.domain.chunk import Chunk
from cora.domain.citations import Source
from cora.domain.errors import InputRejectedError, LlmError, ToolLoopLimitError
from cora.domain.trace import (
    MemoryUnread,
    ModelDecision,
    Reconsidered,
    SecondLookLost,
    ToolUse,
    TraceStep,
)
from cora.engine.steps import (
    GroundStep,
    ModelStep,
    PrepareStep,
    Router,
    ToolStep,
)
from cora.engine.tool_runtime import ToolRuntime
from cora.engine.validation import EmptyInputRule, ValidationPipeline
from cora.ports.chat_model import ChatModel, Message, ModelReply, Role
from cora.ports.plugin import Tool, ToolCall
from fakes import FailingChatModel, FakeContextSource, add_tool

ROUNDS = 8


THREAD = "t1"
_A_STEP = ToolUse(name="add", outcome="3")


def _final(
    runner: LangGraphRunner, state: AgentState, thread_id: str = THREAD
) -> AgentState:
    return list(runner.run(state, thread_id))[-1]


def _answered(state: AgentState) -> bool:
    """A round has been spent this turn: the fake steps read the transcript for it,
    exactly as the router does."""
    return any(
        message.role == "assistant"
        for message in tuple(state.get("messages", ()))[state.get("turn_start", 0) :]
    )


def _said(role: Role, content: str) -> list[Message]:
    return [Message(role=role, content=content)]


def _asked_for_a_tool(content: str) -> list[Message]:
    """A reply the router reads as unfinished: it is asking for a tool."""
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")
    return [Message(role="assistant", content=content, tool_calls=(call,))]


def _prepare(state: AgentState) -> AgentState:
    return {
        "messages": _said("user", state["question"]),
        "turn_start": len(state.get("messages", ())),
        "answer": "",
        "answer_in_hand": "",
        "reconsidered": False,
    }


def _ran(state: AgentState) -> AgentState:
    return {"messages": _said("tool", "ran")}


def _nudge(state: AgentState) -> AgentState:
    return {
        "messages": _said("system", "search first"),
        "answer_in_hand": "off",
        "reconsidered": True,
    }


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
        if _answered(state):
            return {"messages": _said("assistant", "done"), "answer": "d"}
        return {"messages": _asked_for_a_tool("asking")}

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
        if _answered(state):
            return {"messages": _said("assistant", "done"), "answer": "d"}
        return {"messages": _asked_for_a_tool("asking")}

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


def test_an_ungrounded_answer_goes_back_through_the_model() -> None:
    visited: list[str] = []

    def model(state: AgentState) -> AgentState:
        visited.append("model")
        if state.get("reconsidered"):
            return {"messages": _said("assistant", "grounded"), "answer": "grounded"}
        return {"messages": _said("assistant", "off the cuff"), "answer": "off"}

    def ground(state: AgentState) -> AgentState:
        visited.append("ground")
        return {
            "messages": _said("system", "search first"),
            "answer_in_hand": "off",
            "reconsidered": True,
        }

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
        if _answered(state):
            return {"messages": _said("assistant", "done")}
        return {"messages": _asked_for_a_tool("asking")}

    states = _runner(model=model).run({"question": "q"}, THREAD)
    for state in states:
        if _answered(state):
            break

    assert completions == ["round 1"]


def test_a_runaway_graph_surfaces_as_the_friendly_give_up() -> None:
    def endless(state: AgentState) -> AgentState:
        return {"messages": _asked_for_a_tool("again")}

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
        ),
        model=ModelStep(chat_model=model, tools=(add_tool(),), max_history_turns=20),
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


def _replies(state: AgentState) -> AgentState:
    return {"messages": _said("assistant", "ok")}


def test_a_second_run_on_one_thread_starts_where_the_first_finished() -> None:
    """What makes the conversation the graph's rather than the caller's: the second
    turn is seeded with a question alone and finds the first turn already there."""
    runner = _runner(model=_replies)

    _final(runner, {"question": "first"})
    final = _final(runner, {"question": "second"})

    assert [m.content for m in final["messages"]] == ["first", "ok", "second", "ok"]
    assert final["turn_start"] == 2


def test_two_threads_share_nothing() -> None:
    runner = _runner(model=_replies)

    _final(runner, {"question": "mine"}, thread_id="ada")
    final = _final(runner, {"question": "yours"}, thread_id="grace")

    assert [m.content for m in final["messages"]] == ["yours", "ok"]


def test_the_first_state_yielded_is_the_thread_as_the_turn_found_it() -> None:
    """The promise `GraphRunner` makes and `Agent` builds its per-turn slice on: the
    first yield is the thread before any step of this turn ran. Nothing else pins it,
    and a runner that yielded post-step states only would drop each turn's first step
    from the trace with every test still green."""

    def tracing(state: AgentState) -> AgentState:
        return {"messages": _said("assistant", "ok"), "trace": [_A_STEP]}

    runner = _runner(model=tracing)

    _final(runner, {"question": "first"})
    states = list(runner.run({"question": "second"}, THREAD))

    found = states[0]
    assert found["question"] == "second"
    assert [m.content for m in found["messages"]] == ["first", "ok"], (
        "the first yield must predate this turn's prepare"
    )
    assert found["trace"] == [_A_STEP], "and carry only the earlier turn's steps"
    assert len(states[-1]["trace"]) == 2


def test_a_second_turn_round_trips_every_type_the_state_carries() -> None:
    """The state that crosses the checkpoint is core dataclasses — messages, tool
    calls, trace steps, sources. LangGraph allows unregistered types today with a
    logged warning it says will become a block, and a logger warning is invisible to a
    test suite; the runner therefore names what it checkpoints, so an unlisted type
    fails here instead of in a future release. Every trace kind the engine can produce
    is in this state on purpose — one missing from the allowlist breaks a second turn,
    and only a second turn reads a checkpoint back.

    Asserted by kind and by what the step says rather than by equality: msgpack has no
    tuple, so a replayed `tools=("add",)` comes back `["add"]`. Nothing reads those
    fields for anything but iteration and truthiness, and the prompt is built from
    fresh messages, so the flattening costs nothing — but it is why a replayed step is
    not `==` to the one that was written."""

    every_kind: list[TraceStep] = [
        ModelDecision(detail="thinking", tools=("add",)),
        ToolUse(name="add", arguments={"a": 1}, outcome="3"),
        Reconsidered(outcome="1 passage"),
        SecondLookLost(),
        MemoryUnread(),
    ]

    def tracing(state: AgentState) -> AgentState:
        if _answered(state):
            return {"messages": _said("assistant", "done"), "answer": "done"}
        return {
            "messages": _asked_for_a_tool("ok"),
            "trace": list(every_kind),
            "sources": [Source(1, "note.md")],
        }

    runner = _runner(model=tracing)

    _final(runner, {"question": "first"})
    final = _final(runner, {"question": "second"})

    assert [m.content for m in final["messages"]][:2] == ["first", "ok"]
    assert final["messages"][1].tool_calls[0].name == "add"
    assert final["sources"] == [Source(1, "note.md"), Source(1, "note.md")]

    replayed = final["trace"][: len(every_kind)]
    assert [type(step) for step in replayed] == [type(step) for step in every_kind]
    assert [step.summary for step in replayed] == [step.summary for step in every_kind]
    assert [step.failed for step in replayed] == [step.failed for step in every_kind]


def test_the_allowlist_covers_every_kind_of_step_a_trace_can_hold() -> None:
    """The guard the round-trip test cannot be: a `TraceStep` added next sprint would
    checkpoint fine on today's permissive default and break the first turn after
    LangGraph makes good on blocking unregistered types."""
    listed = set(checkpointed_types())

    for kind in _trace_kinds():
        assert (kind.__module__, kind.__name__) in listed, (
            f"{kind.__name__} can be in a trace but not in a checkpoint"
        )
    assert {kind.__name__ for kind in _trace_kinds()} >= {
        "ModelDecision",
        "Reconsidered",
        "SecondLookLost",
        "MemoryUnread",
        "ToolUse",
    }, "the walk found fewer kinds than the engine ships"


def test_an_unlisted_type_does_not_come_back_as_itself() -> None:
    """What makes the allowlist a decision rather than a comment. Asked of the saver the
    runner actually builds, not of a serializer a test made: LangGraph's default is
    permissive, so a runner that forgot the allowlist would pass every round-trip test
    there is and fail the first turn after the default changes."""
    serde = _runner(model=_replies).checkpointer.serde

    declared = serde.loads_typed(serde.dumps_typed(Message(role="user", content="hi")))
    undeclared = serde.loads_typed(
        serde.dumps_typed(Chunk(text="t", source="s.md", index=0, offset=0))
    )

    assert isinstance(declared, Message)
    assert (declared.role, declared.content) == ("user", "hi")
    assert not isinstance(undeclared, Chunk)
