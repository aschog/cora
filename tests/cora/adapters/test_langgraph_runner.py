from pathlib import Path
from typing import Any

import pytest

from cora.adapters.langgraph_runner import (
    LangGraphRunner,
    checkpointed_types,
    interrupting,
    langgraph_for,
    recursion_limit_for,
)
from cora.domain.agent_state import AgentState
from cora.domain.card import Answer
from cora.domain.citations import Citation
from cora.domain.errors import (
    ToolLoopLimitError,
)
from cora.domain.trace import (
    HandlerRan,
    MemoryUnread,
    ModelDecision,
    StepEntered,
    ToolUse,
    TraceStep,
    step_kinds,
)
from cora.engine.ask_tool import ASK_TOOL_NAME
from cora.engine.steps import (
    ANSWER,
    SCREEN,
    WORK,
    AnswerStep,
    AskStep,
    GateStep,
    Named,
    Router,
    opening,
)
from cora.ports.chat_model import (
    Message,
    Role,
    TextSink,
    unheard,
)
from cora.ports.graph import Loop, ModelFor, NamedStep, Step
from cora.ports.plugin import Tool, ToolCall

ROUNDS = 8


THREAD = "t1"
NOTE = Citation(number=1, document="note.md", start=0, end=7)


def _final(
    runner: LangGraphRunner,
    state: AgentState,
    thread_id: str = THREAD,
    on_text: TextSink = unheard,
) -> AgentState:
    return list(runner.run(state, thread_id, on_text))[-1]


def _answered(state: AgentState) -> bool:
    return any(
        message.role == "assistant"
        for message in tuple(state.get("messages", ()))[state.get("turn_start", 0) :]
    )


def _said(role: Role, content: str) -> list[Message]:
    return [Message(role=role, content=content)]


def _asked_for_a_tool(content: str) -> list[Message]:
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")
    return [Message(role="assistant", content=content, tool_calls=(call,))]


def _screen(state: AgentState) -> AgentState:
    return {
        "messages": _said("user", state["question"]),
        "turn_start": len(state.get("messages", ())),
        "answer": "",
    }


def _ran(state: AgentState) -> AgentState:
    return {"messages": _said("tool", "ran")}


def _always(step: Step) -> ModelFor:
    return lambda _on_text: step


def _nothing(state: AgentState) -> AgentState:
    return {}


STEPS = 3


def _walk(
    model: ModelFor,
    *,
    screen: Step = _screen,
    gate: Step | None = None,
    tools: Step = _ran,
    ask: Step = _nothing,
    rounds: int = ROUNDS,
    after: tuple[NamedStep, ...] = (Named(ANSWER, AnswerStep()),),
) -> dict[str, Any]:
    return {
        "before": (Named(SCREEN, screen),),
        "loop": Loop(
            marker=Named(WORK),
            opening=opening,
            model=model,
            gate=GateStep() if gate is None else gate,
            tools=tools,
            ask=ask,
            router=Router(max_tool_rounds=rounds),
        ),
        "after": after,
    }


def _runner(
    *,
    screen: Step = _screen,
    model: ModelFor,
    gate: Step | None = None,
    tools: Step = _ran,
    ask: Step = _nothing,
    rounds: int = ROUNDS,
    recursion_limit: int | None = None,
) -> LangGraphRunner:
    return LangGraphRunner(
        **_walk(model, screen=screen, gate=gate, tools=tools, ask=ask, rounds=rounds),
        recursion_limit=recursion_limit or recursion_limit_for(rounds, steps=STEPS),
    )


def test_the_graph_is_built_from_the_walk_of_a_turn_alone() -> None:
    """`langgraph_for` is the `GraphFor` slot, so what it accepts is the port itself: a
    turn is handed over as its walk, and nothing else is something a composition root
    can hand it."""
    walk = _walk(_always(_replies))

    assert isinstance(langgraph_for(**walk, max_tool_rounds=8), LangGraphRunner)

    with pytest.raises(TypeError):
        langgraph_for(
            **walk,
            ground=_ran,  # ty: ignore[unknown-argument]
            max_tool_rounds=8,
        )


def test_run_walks_screen_then_model_then_tools_then_model() -> None:
    visited: list[str] = []

    def screening(state: AgentState) -> AgentState:
        visited.append(SCREEN)
        return _screen(state)

    def model(state: AgentState) -> AgentState:
        visited.append("model")
        if _answered(state):
            return {"messages": _said("assistant", "done")}
        return {"messages": _asked_for_a_tool("asking")}

    def tools(state: AgentState) -> AgentState:
        visited.append("tools")
        return {"messages": _said("tool", "ran")}

    final = _final(
        _runner(screen=screening, model=_always(model), tools=tools), {"question": "q"}
    )

    assert visited == [SCREEN, "model", "tools", "model"]
    assert final["answer"] == "done"


def test_a_runaway_graph_surfaces_as_the_friendly_give_up() -> None:
    def endless(state: AgentState) -> AgentState:
        return {"messages": _asked_for_a_tool("again")}

    runner = _runner(model=_always(endless), rounds=999, recursion_limit=4)

    with pytest.raises(ToolLoopLimitError):
        _final(runner, {"question": "q"})


def _replies(state: AgentState) -> AgentState:
    return {"messages": _said("assistant", "ok")}


def test_two_threads_share_nothing() -> None:
    runner = _runner(model=_always(_replies))

    _final(runner, {"question": "mine"}, thread_id="ada")
    final = _final(runner, {"question": "yours"}, thread_id="grace")

    assert [m.content for m in final["messages"]] == ["yours", "ok"]


def test_a_second_turn_round_trips_every_type_the_state_carries() -> None:
    """The state that crosses the checkpoint is core dataclasses — messages, tool calls,
    trace steps, sources. LangGraph allows unregistered types today with a logged
    warning it says will become a block, and a logger warning is invisible to a test
    suite, so the runner names what it checkpoints. Every trace kind the engine can
    produce is in this state on purpose: one missing from the allowlist breaks a second
    turn.

    Asserted by kind and by what the step says rather than by equality: msgpack has no
    tuple, so a replayed `tools=("add",)` comes back `["add"]`. Nothing reads those
    fields for anything but iteration and truthiness, which is why the flattening costs
    nothing — and why a replayed step is not `==` to the one that was written.
    """

    every_kind: list[TraceStep] = [
        ModelDecision(detail="thinking", tools=("add",)),
        ToolUse(name="add", arguments={"a": 1}, outcome="3"),
        MemoryUnread(),
        HandlerRan(plugin="plug", event="brief", outcome="amended the brief"),
    ]

    def tracing(state: AgentState) -> AgentState:
        if _answered(state):
            return {"messages": _said("assistant", "done")}
        return {
            "messages": _asked_for_a_tool("ok"),
            "trace": list(every_kind),
            "citations": [NOTE],
        }

    runner = _runner(model=_always(tracing))

    _final(runner, {"question": "first"})
    final = _final(runner, {"question": "second"})

    assert [m.content for m in final["messages"]][:2] == ["first", "ok"]
    assert final["messages"][1].tool_calls[0].name == "add"
    assert final["citations"] == [NOTE, NOTE]

    walked = [step for step in final["trace"] if not isinstance(step, StepEntered)]
    replayed = walked[: len(every_kind)]
    assert [type(step) for step in replayed] == [type(step) for step in every_kind]
    assert [step.summary for step in replayed] == [step.summary for step in every_kind]
    assert [step.failed for step in replayed] == [step.failed for step in every_kind]


def test_the_allowlist_covers_every_kind_of_step_a_trace_can_hold() -> None:
    """The guard the round-trip test cannot be: a `TraceStep` added next sprint would
    checkpoint fine on today's permissive default and break the first turn after
    LangGraph makes good on blocking unregistered types."""
    listed = set(checkpointed_types())

    for kind in step_kinds():
        assert (kind.__module__, kind.__name__) in listed, (
            f"{kind.__name__} can be in a trace but not in a checkpoint"
        )
    assert {kind.__name__ for kind in step_kinds()} >= {
        "StepEntered",
        "ModelDecision",
        "MemoryUnread",
        "ToolUse",
        "WorkShown",
    }, "the walk found fewer kinds than the engine ships"


# ── a run that stops to ask ──

ASKED_AT_THE_NODE = "Which bodyweight should I treat as current?"
WANTED = "What is my BMR?"


def _asks_then_answers(state: AgentState) -> AgentState:
    if _answered(state):
        return {"messages": _said("assistant", "done")}
    call = ToolCall(
        name=ASK_TOOL_NAME,
        arguments={
            "question": ASKED_AT_THE_NODE,
            "options": [{"label": "77 kg"}, {"label": "75 kg", "note": "February"}],
            "decline": "Neither",
        },
        call_id="a1",
    )
    return {"messages": [Message(role="assistant", content="", tool_calls=(call,))]}


def _stopping(rounds: int = ROUNDS) -> LangGraphRunner:
    return _runner(
        model=_always(_asks_then_answers),
        tools=_nothing,
        ask=AskStep(pause=interrupting),
        rounds=rounds,
    )


def _answers(state: AgentState) -> tuple[str, ...]:
    return tuple(
        message.content
        for message in state.get("messages", ())
        if message.role == "tool"
    )


def test_a_run_that_stops_to_ask_parks_what_it_stopped_on() -> None:
    """The pause is not something the caller can see go past: the stream simply ends,
    so what the thread is waiting on has to be read back off the checkpoint."""
    runner = _stopping()

    list(runner.run({"question": WANTED}, THREAD))

    waiting = runner.pending(THREAD)
    assert waiting is not None
    assert waiting.asked == WANTED
    assert waiting.card.prompt == ASKED_AT_THE_NODE
    assert [action.label for action in waiting.card.actions] == [
        "77 kg",
        "75 kg",
        "Neither",
    ]


def test_resuming_hands_the_answer_back_into_the_step_that_asked() -> None:
    runner = _stopping()
    list(runner.run({"question": WANTED}, THREAD))

    final = list(runner.resume(Answer(action="75 kg"), THREAD))[-1]

    assert final["answer"] == "done"
    assert _answers(final) == ("75 kg",)
    assert runner.pending(THREAD) is None, "the thread is waiting on nothing now"


def test_a_thread_is_forgotten_out_of_the_file_a_deployment_keeps_it_in(
    tmp_path: Path,
) -> None:
    """The checkpointer a deployment runs is the file-backed one, and it is the one a
    delete has to reach: in memory a thread dies with the process anyway."""
    path = str(tmp_path / "conversations.sqlite")
    first = langgraph_for(
        **_walk(_always(_replies)), max_tool_rounds=ROUNDS, checkpoints_at=path
    )
    list(first.run({"question": WANTED, "pin": "fitness"}, THREAD))

    first.forget(THREAD)

    second = langgraph_for(
        **_walk(_always(_replies)), max_tool_rounds=ROUNDS, checkpoints_at=path
    )
    assert second.pinned(THREAD) is None


# ── the walk itself ──


BOOKED = "book_it"
BOOKING = "Book the thing, which cannot be taken back"


def _effecting(name: str) -> Tool:
    return Tool(
        name=name,
        description=BOOKING,
        parameter_schema={"type": "object"},
        run=lambda **_: name,
        effect=True,
    )


def _proposes(*names: str) -> Step:
    def model(state: AgentState) -> AgentState:
        if _answered(state):
            return {"messages": _said("assistant", "done")}
        calls = tuple(
            ToolCall(name=name, arguments={}, call_id=f"c{at}")
            for at, name in enumerate(names, start=1)
        )
        return {"messages": [Message(role="assistant", content="", tool_calls=calls)]}

    return model


def _gated(*names: str) -> tuple[LangGraphRunner, list[str]]:
    ran: list[str] = []
    tools = tuple(_effecting(name) for name in names)

    def running(state: AgentState) -> AgentState:
        """The round's outstanding calls, read the way `ToolStep` reads them: what the
        last assistant message asked for, minus whatever a `tool` message has settled —
        so a call the gate answered is one this never sees."""
        asked: tuple[ToolCall, ...] = ()
        answered: set[str] = set()
        for message in state.get("messages", ()):
            if message.role == "assistant":
                asked, answered = message.tool_calls, set()
            elif message.tool_call_id is not None:
                answered.add(message.tool_call_id)
        messages = []
        for call in asked:
            if call.call_id in answered:
                continue
            ran.append(call.name)
            messages.append(
                Message(role="tool", content="ran", tool_call_id=call.call_id)
            )
        return {"messages": messages}

    runner = langgraph_for(
        before=(Named(SCREEN, _screen),),
        loop=Loop(
            marker=Named(WORK),
            opening=opening,
            model=_always(_proposes(*names)),
            gate=GateStep(tools=tools, approve=interrupting),
            tools=running,
            ask=_nothing,
            router=Router(max_tool_rounds=ROUNDS),
        ),
        after=(Named(ANSWER, AnswerStep()),),
        max_tool_rounds=ROUNDS,
    )
    assert isinstance(runner, LangGraphRunner)
    return runner, ran


def test_an_approved_effect_runs_once_and_the_turn_answers() -> None:
    runner, ran = _gated(BOOKED)
    list(runner.run({"question": "book it"}, THREAD))

    final = list(runner.resume(Answer(action="c1"), THREAD))[-1]

    assert ran == [BOOKED]
    assert final["answer"] == "done"
    assert runner.pending(THREAD) is None
