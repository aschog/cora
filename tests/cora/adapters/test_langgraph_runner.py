import threading
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from cora.adapters.langgraph_runner import (
    HEADROOM,
    LangGraphRunner,
    checkpointed_types,
    interrupting,
    langgraph_for,
    recursion_limit_for,
)
from cora.domain.agent_state import AgentState
from cora.domain.approval import Proposed
from cora.domain.card import Answer
from cora.domain.chunk import Chunk
from cora.domain.citations import Citation
from cora.domain.errors import (
    InputRejectedError,
    LlmError,
    NothingToResumeError,
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
from cora.engine.plugin_set import Registry
from cora.engine.steps import (
    ANSWER,
    DECLINED_CALL,
    NOTHING_CHOSEN,
    SCREEN,
    WORK,
    AnswerStep,
    AskStep,
    GateStep,
    ModelStep,
    Named,
    Router,
    ScreenStep,
    ToolStep,
)
from cora.engine.tool_runtime import ToolRuntime
from cora.engine.validation import CORA, refuse_nothing_to_answer
from cora.ports.chat_model import (
    ChatModel,
    Message,
    ModelReply,
    Piece,
    Role,
    TextSink,
    Written,
    unheard,
)
from cora.ports.graph import Loop, ModelFor, NamedStep, Step
from cora.ports.host import (
    HANDLER,
    INSTRUCTIONS,
    SCREENING,
    Registration,
    Subscription,
)
from cora.ports.plugin import Tool, ToolCall
from fakes import FailingChatModel, ScriptedChatModel, add_tool

ROUNDS = 8


THREAD = "t1"
_A_STEP = ToolUse(name="add", outcome="3")
NOTE = Citation(number=1, document="note.md", start=0, end=7)


def _final(
    runner: LangGraphRunner,
    state: AgentState,
    thread_id: str = THREAD,
    on_text: TextSink = unheard,
) -> AgentState:
    return list(runner.run(state, thread_id, on_text))[-1]


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


def _screen(state: AgentState) -> AgentState:
    return {
        "messages": _said("user", state["question"]),
        "turn_start": len(state.get("messages", ())),
        "answer": "",
    }


def _ran(state: AgentState) -> AgentState:
    return {"messages": _said("tool", "ran")}


def _always(step: Step) -> ModelFor:
    """A model slot that writes nowhere: what a step with nothing to say to the reader
    looks like when the graph asks for one per turn."""
    return lambda _on_text: step


def _nothing(state: AgentState) -> AgentState:
    return {}


STEPS = 3
"""What a turn walks besides its rounds: it screens, it works, and it answers."""


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
    """The named steps of a turn, with a fake in each place a test wants to watch.

    The gate is the real one unless a test says otherwise: with no effecting tool in
    front of it there is nothing for it to stop, which is what a round that changes
    nothing outside cora looks like going past it.
    """
    return {
        "before": (Named(SCREEN, screen),),
        "loop": Loop(
            marker=Named(WORK),
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


def test_the_returned_state_accumulated_every_partial() -> None:
    def model(state: AgentState) -> AgentState:
        if _answered(state):
            return {"messages": _said("assistant", "done")}
        return {"messages": _asked_for_a_tool("asking")}

    def tools(state: AgentState) -> AgentState:
        return {
            "messages": _said("tool", "ran"),
            "trace": [ToolUse(name="search_documents", outcome="1 passage")],
            "citations": [NOTE],
        }

    final = _final(_runner(model=_always(model), tools=tools), {"question": "q"})

    assert [m.content for m in final["messages"]] == ["q", "asking", "ran", "done"]
    assert final["trace"] == [
        StepEntered(SCREEN),
        StepEntered(WORK),
        ToolUse(name="search_documents", outcome="1 passage"),
        StepEntered(ANSWER),
    ]
    assert final["citations"] == [NOTE]


def test_an_answer_ends_the_rounds_and_the_walk_goes_on() -> None:
    """A final reply is the end of the *rounds*, whatever the answer rested on: the
    turn leaves the loop for the step that settles what the user reads, and stops
    there."""
    visited: list[str] = []

    def model(state: AgentState) -> AgentState:
        visited.append("model")
        return {"messages": _said("assistant", "off the cuff")}

    final = _final(_runner(model=_always(model)), {"question": "q"})

    assert visited == ["model"], "one round, and nothing sent it back for another"
    assert _entered(final) == [SCREEN, WORK, ANSWER]
    assert final["answer"] == "off the cuff"


def test_a_caller_sees_a_rounds_decision_before_the_turn_has_finished() -> None:
    """Pull states until the first round's decision shows up: the second round must
    not have run yet, or the caller is being handed a finished run."""
    completions: list[str] = []

    def model(state: AgentState) -> AgentState:
        completions.append(f"round {len(completions) + 1}")
        if _answered(state):
            return {"messages": _said("assistant", "done")}
        return {
            "messages": _asked_for_a_tool("asking"),
            "trace": [ModelDecision(detail="asking", tools=("add",))],
        }

    states = _runner(model=_always(model)).run({"question": "q"}, THREAD)
    for state in states:
        if any(isinstance(step, ModelDecision) for step in state.get("trace", ())):
            break

    assert completions == ["round 1"]


def test_a_runaway_graph_surfaces_as_the_friendly_give_up() -> None:
    def endless(state: AgentState) -> AgentState:
        return {"messages": _asked_for_a_tool("again")}

    runner = _runner(model=_always(endless), rounds=999, recursion_limit=4)

    with pytest.raises(ToolLoopLimitError):
        _final(runner, {"question": "q"})


class _AlwaysCalling:
    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
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


def _screening() -> Registry:
    """Cora's own screen and a plugin's instructions, as an assembled app wires them."""
    return Registry(
        (
            Registration(
                module=CORA,
                kind=HANDLER,
                value=Subscription(event=SCREENING, handle=refuse_nothing_to_answer),
            ),
            Registration(
                module="fixture_plugins.valid", kind=INSTRUCTIONS, value="SYS"
            ),
        )
    )


def _real_runner(model: ChatModel, rounds: int) -> LangGraphRunner:
    """The walk as the composition root wires it, with a real model behind it."""
    return LangGraphRunner(
        before=(Named(SCREEN, ScreenStep(registry=_screening())),),
        loop=Loop(
            marker=Named(WORK),
            model=ModelStep(
                chat_model=model, tools=(add_tool(),), max_history_turns=20
            ).writing_to,
            gate=GateStep(tools=(add_tool(),)),
            tools=ToolStep(ToolRuntime(tools=(add_tool(),))),
            router=Router(max_tool_rounds=rounds),
            ask=AskStep(),
        ),
        after=(Named(ANSWER, AnswerStep()),),
        recursion_limit=recursion_limit_for(rounds, steps=STEPS),
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


def test_an_input_rejection_from_screen_travels_out_unwrapped() -> None:
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
    runner = _runner(model=_always(_replies))

    _final(runner, {"question": "first"})
    final = _final(runner, {"question": "second"})

    assert [m.content for m in final["messages"]] == ["first", "ok", "second", "ok"]
    assert final["turn_start"] == 2


def test_two_threads_share_nothing() -> None:
    runner = _runner(model=_always(_replies))

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

    runner = _runner(model=_always(tracing))

    _final(runner, {"question": "first"})
    states = list(runner.run({"question": "second"}, THREAD))

    found = states[0]
    assert found["question"] == "second"
    assert [m.content for m in found["messages"]] == ["first", "ok"], (
        "the first yield must predate this turn's screening"
    )
    assert found["trace"] == [
        StepEntered(SCREEN),
        StepEntered(WORK),
        _A_STEP,
        StepEntered(ANSWER),
    ], "and carry only the earlier turn's steps"
    assert len(states[-1]["trace"]) == 8, "and the second turn adds its own four"


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
    }, "the walk found fewer kinds than the engine ships"


def test_an_unlisted_type_does_not_come_back_as_itself() -> None:
    """What makes the allowlist a decision rather than a comment. Asked of the saver the
    runner actually builds, not of a serializer a test made: LangGraph's default is
    permissive, so a runner that forgot the allowlist would pass every round-trip test
    there is and fail the first turn after the default changes."""
    serde = _runner(model=_always(_replies)).checkpointer.serde

    declared = serde.loads_typed(serde.dumps_typed(Message(role="user", content="hi")))
    undeclared = serde.loads_typed(
        serde.dumps_typed(Chunk(text="t", source="s.md", index=0, offset=0))
    )

    assert isinstance(declared, Message)
    assert (declared.role, declared.content) == ("user", "hi")
    assert not isinstance(undeclared, Chunk)


@pytest.mark.integration
def test_a_thread_resumed_in_a_second_runner_carries_what_the_model_was_told(
    tmp_path: Path,
) -> None:
    """Reopening a conversation is not just redrawing it: the follow-up question is
    asked of a model that has to remember the exchange before it. In memory that ends
    with the process, so the checkpoint goes where the deployment says."""
    path = str(tmp_path / "conversations.sqlite")
    seen: list[list[str]] = []

    def remembering(state: AgentState) -> AgentState:
        seen.append([message.content for message in state.get("messages", ())])
        return {"messages": _said("assistant", "answered")}

    first = langgraph_for(
        **_walk(_always(remembering)), max_tool_rounds=ROUNDS, checkpoints_at=path
    )
    list(first.run({"question": "How much protein?"}, THREAD))

    second = langgraph_for(
        **_walk(_always(remembering)), max_tool_rounds=ROUNDS, checkpoints_at=path
    )
    list(second.run({"question": "And creatine?"}, THREAD))

    assert "How much protein?" in seen[-1], (
        f"the resumed thread forgot the exchange before it: {seen[-1]}"
    )


def test_a_runner_told_no_path_keeps_its_thread_in_memory() -> None:
    """The default is unchanged: a deployment that names no file gets a thread that
    lives as long as the process, as every test here relies on."""
    runner = langgraph_for(**_walk(_always(_replies)), max_tool_rounds=ROUNDS)

    assert isinstance(runner, LangGraphRunner)
    assert isinstance(runner.checkpointer, InMemorySaver)


def _writing(*pieces: str) -> ModelFor:
    """The model slot as assembly fills it: asked for a step per turn, and the step it
    hands back writes to that turn's reader."""

    def bound(on_text: TextSink) -> Step:
        def step(state: AgentState) -> AgentState:
            for piece in pieces:
                on_text(Piece(piece))
            written = "".join(pieces)
            return {"messages": _said("assistant", written)}

        return step

    return bound


def test_a_run_hands_the_model_node_the_sink_it_was_asked_with() -> None:
    """The answer is written inside a step, and a graph yields only between steps — so
    the only way out for it is the sink the run carries in."""
    written: list[Written] = []
    runner = _runner(model=_writing("Sleep, ", "not volume."))

    _final(runner, {"question": "why"}, on_text=written.append)

    assert written == [Piece("Sleep, "), Piece("not volume.")]


def _writing_its_question(both: threading.Barrier) -> ModelFor:
    """A model that writes the question it was asked, in two pieces, holding between
    them until the other run has written its first — so the two runs are inside the
    model node at the same time, which is the only state in which they can cross."""

    def bound(on_text: TextSink) -> Step:
        def step(state: AgentState) -> AgentState:
            asked = state["question"]
            on_text(Piece(f"{asked} first"))
            both.wait()
            on_text(Piece(f"{asked} last"))
            written = f"{asked} first{asked} last"
            return {"messages": _said("assistant", written)}

        return step

    return bound


def test_two_runs_of_one_runner_do_not_cross() -> None:
    """One assembled app answers two readers, each on their own thread and their own
    worker. A sink shared between them would send each the other's answer — which two
    runs taken in turn cannot show: a sink kept on the runner and rebound per run passes
    that, and crosses the moment two readers overlap. So they overlap here, and each
    model node writes the question its own run carried in."""
    both = threading.Barrier(2, timeout=5)
    written: dict[str, list[Written]] = {"ada": [], "grace": []}
    runner = _runner(model=_writing_its_question(both))

    readers = [
        threading.Thread(
            target=_final, args=(runner, {"question": who}, who, written[who].append)
        )
        for who in written
    ]
    for reader in readers:
        reader.start()
    for reader in readers:
        reader.join(timeout=10)

    assert written == {
        "ada": [Piece("ada first"), Piece("ada last")],
        "grace": [Piece("grace first"), Piece("grace last")],
    }


def test_a_run_asked_with_no_sink_takes_the_same_turn() -> None:
    final = _final(_runner(model=_writing("ok")), {"question": "why"})

    assert final["answer"] == "ok"


def test_a_decision_travels_through_a_checkpoint_as_itself() -> None:
    """A pause lives in the checkpointer until it is picked up, so the card is only ever
    as good as the allowlist: an unlisted type comes back a dict on the day LangGraph
    makes good on refusing what it was not told about."""
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    from cora.domain.decision import Decision, Option

    settled = Decision(
        question="Which bodyweight should I treat as current?",
        options=(Option(label="75 kg", note="coach notes, February"),),
        decline="Neither",
    )
    serde = JsonPlusSerializer(allowed_msgpack_modules=checkpointed_types())

    back = serde.loads_typed(serde.dumps_typed(settled))

    assert isinstance(back, Decision)
    assert back.question == settled.question
    assert back.decline == settled.decline
    assert [(option.label, option.note) for option in back.options] == [
        ("75 kg", "coach notes, February")
    ], "the options are read back one by one, as a sequence of Options"


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


def test_declining_arrives_at_the_step_as_nothing_chosen() -> None:
    runner = _stopping()
    list(runner.run({"question": WANTED}, THREAD))

    final = list(runner.resume(Answer(), THREAD))[-1]

    assert _answers(final) == (NOTHING_CHOSEN,)
    assert final["answer"] == "done"


def test_resuming_a_thread_with_nothing_parked_is_refused_as_a_core_error() -> None:
    """A card clicked twice, or one left open while the conversation moved on. The
    shell already turns a `CoreError` into a sentence; a library error is a
    traceback."""
    runner = _stopping()

    with pytest.raises(NothingToResumeError):
        list(runner.resume(Answer(action="75 kg"), THREAD))


def test_a_thread_that_never_stopped_is_waiting_on_nothing() -> None:
    runner = _stopping()

    assert runner.pending(THREAD) is None


def test_a_forgotten_thread_holds_no_pin() -> None:
    runner = _runner(model=_always(_replies))
    list(runner.run({"question": WANTED, "pin": "fitness"}, THREAD))
    assert runner.pinned(THREAD) == "fitness"

    runner.forget(THREAD)

    assert runner.pinned(THREAD) is None


def test_a_forgotten_thread_is_waiting_on_nothing() -> None:
    runner = _stopping()
    list(runner.run({"question": WANTED}, THREAD))
    assert runner.pending(THREAD) is not None

    runner.forget(THREAD)

    assert runner.pending(THREAD) is None


def test_resuming_a_forgotten_thread_is_refused_as_a_thread_waiting_on_nothing() -> (
    None
):
    """The card was answered after its conversation was deleted, which is the same
    nothing as a card clicked twice."""
    runner = _stopping()
    list(runner.run({"question": WANTED}, THREAD))
    runner.forget(THREAD)

    with pytest.raises(NothingToResumeError):
        list(runner.resume(Answer(action="75 kg"), THREAD))


def test_forgetting_one_thread_leaves_the_others() -> None:
    runner = _runner(model=_always(_replies))
    list(runner.run({"question": WANTED, "pin": "fitness"}, "kept"))
    list(runner.run({"question": WANTED, "pin": "travel"}, "gone"))

    runner.forget("gone")

    assert runner.pinned("kept") == "fitness"


def test_forgetting_a_thread_nobody_has_asked_anything_on_is_not_an_error() -> None:
    runner = _runner(model=_always(_replies))

    runner.forget(THREAD)

    assert runner.pinned(THREAD) is None


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


def test_a_turn_that_stops_to_ask_still_gets_its_whole_round_budget() -> None:
    """The pause costs a superstep of its own, so a limit sized for rounds alone would
    make a turn that stopped to check look like a runaway one."""
    runner = _stopping(rounds=1)
    list(runner.run({"question": WANTED}, THREAD))

    final = list(runner.resume(Answer(action="75 kg"), THREAD))[-1]

    assert final["answer"] == "done"


def test_a_turn_that_keeps_asking_is_stopped_by_the_round_budget() -> None:
    """The pause is visited once a turn, so a limit sized for one ask still holds: a
    model that asks again is routed to the tools, where the engine's own budget stops
    it — rather than the graph overrunning a limit that never expected a second."""
    rounds = 0

    def asks(state: AgentState) -> AgentState:
        nonlocal rounds
        rounds += 1
        call = ToolCall(
            name=ASK_TOOL_NAME,
            arguments={
                "question": "Which bodyweight?",
                "options": [{"label": "77 kg"}, {"label": "75 kg"}],
            },
            call_id=f"a{rounds}",
        )
        return {"messages": [Message(role="assistant", content="", tool_calls=(call,))]}

    runner = _runner(
        model=_always(asks),
        tools=_nothing,
        ask=AskStep(pause=interrupting),
        rounds=2,
    )
    list(runner.run({"question": "q"}, THREAD))

    with pytest.raises(ToolLoopLimitError):
        list(runner.resume(Answer(action="77 kg"), THREAD))

    assert rounds == 2, "exactly the rounds the budget allows, and no more"


# ── the walk itself ──


def _adds(call_id: str) -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id=call_id),)
    )


def _entered(state: AgentState) -> list[str]:
    """The steps this state says the turn has been in, in the order it entered them."""
    return [
        step.step for step in state.get("trace", ()) if isinstance(step, StepEntered)
    ]


def test_a_turn_walks_screen_then_work_then_answer_a_state_at_a_time() -> None:
    """The story's whole claim, off a real walk: three named steps, in that order, and
    a state handed back as each of them is taken."""
    runner = _real_runner(ScriptedChatModel([ModelReply(text="ok")]), rounds=ROUNDS)

    walked = [_entered(state) for state in runner.run({"question": "q"}, THREAD)]

    assert walked == [
        [],  # the thread as the turn found it
        [SCREEN],
        [SCREEN, WORK],
        [SCREEN, WORK],  # the round, which is the loop's and not a step of its own
        [SCREEN, WORK, ANSWER],
    ]


def test_every_round_falls_inside_the_working_step() -> None:
    model = ScriptedChatModel([_adds("c1"), _adds("c2"), ModelReply(text="3 and 3.")])

    final = _final(_real_runner(model, rounds=ROUNDS), {"question": "add 1 and 2"})

    trace = final["trace"]
    rounds = [
        at for at, step in enumerate(trace) if isinstance(step, ModelDecision | ToolUse)
    ]
    assert len(rounds) == 5, "three decisions and the two calls they asked for"
    assert trace.index(StepEntered(WORK)) < min(rounds)
    assert max(rounds) < trace.index(StepEntered(ANSWER))


def test_the_steps_either_side_of_the_rounds_take_none() -> None:
    """Screening and answering read the state; neither reaches the model, so a turn
    costs exactly the rounds the loop spent."""
    model = ScriptedChatModel([_adds("c1"), ModelReply(text="3.")])

    final = _final(_real_runner(model, rounds=ROUNDS), {"question": "add 1 and 2"})

    assert model.completions == 2
    assert [message.role for message in final["messages"]] == [
        "user",
        "assistant",
        "tool",
        "assistant",
    ]
    assert final["answer"] == "3."


def test_the_transcript_holds_one_copy_of_the_question_and_of_each_message() -> None:
    """The walk accumulates as the thread does, and nothing on it is replayed: a second
    turn finds the first exactly once."""
    model = ScriptedChatModel(
        [_adds("c1"), ModelReply(text="3."), ModelReply(text="Still 3.")]
    )
    runner = _real_runner(model, rounds=ROUNDS)

    _final(runner, {"question": "add 1 and 2"})
    final = _final(runner, {"question": "and again?"})

    assert [(m.role, m.content) for m in final["messages"]] == [
        ("user", "add 1 and 2"),
        ("assistant", ""),
        ("tool", "3"),
        ("assistant", "3."),
        ("user", "and again?"),
        ("assistant", "Still 3."),
    ]


def test_a_turn_parks_from_inside_the_working_step() -> None:
    """Where the pause happens is what makes it *work*'s: the turn is in that step when
    it stops, and the thread says so while it waits."""
    runner = _stopping()

    states = list(runner.run({"question": WANTED}, THREAD))

    assert runner.pending(THREAD) is not None
    assert _entered(states[-1]) == [SCREEN, WORK], "parked in the working step"


def test_a_resumed_turn_does_not_run_the_tool_that_ran_before_it_stopped() -> None:
    """A resumed node is replayed from its first line, so a round that had already run
    a tool must not run it again on the way back."""
    ran: list[str] = []

    def counted(a: int, b: int) -> int:
        ran.append("add")
        return a + b

    counting = replace(add_tool(), run=counted)

    def model(state: AgentState) -> AgentState:
        rounds = sum(
            1 for message in state.get("messages", ()) if message.role == "assistant"
        )
        if rounds == 0:
            return {"messages": _asked_for_a_tool("first, the tool")}
        if rounds == 1:
            return _asks_then_answers({})
        return {"messages": _said("assistant", "done")}

    runner = _runner(
        model=_always(model),
        tools=ToolStep(ToolRuntime(tools=(counting,))),
        ask=AskStep(pause=interrupting),
    )
    list(runner.run({"question": WANTED}, THREAD))

    assert ran == ["add"], "the pause came after the tool of the first round"

    final = list(runner.resume(Answer(action="75 kg"), THREAD))[-1]

    assert ran == ["add"], "and the resumed turn did not run it a second time"
    assert final["answer"] == "done"


class _BreaksOnTheSecondRound:
    """A model that reaches a tool and then cannot be reached itself: the shape of a
    turn that fails with a round already spent."""

    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        self.completions += 1
        if self.completions == 1:
            return _adds("c1")
        if self.completions == 2:
            raise LlmError()
        return ModelReply(text="Three.")


def test_a_thread_whose_turn_failed_part_way_answers_the_next_question() -> None:
    """A failed turn is not a broken thread: the next question is answered on it."""
    runner = _real_runner(_BreaksOnTheSecondRound(), rounds=ROUNDS)

    with pytest.raises(LlmError):
        _final(runner, {"question": "add 1 and 2"})

    assert _final(runner, {"question": "what was that?"})["answer"] == "Three."


def test_what_was_said_before_a_failure_is_still_on_the_thread() -> None:
    """Every step that finished is checkpointed as it finishes, so the round the turn
    did spend is on the thread the next question is asked of."""
    runner = _real_runner(_BreaksOnTheSecondRound(), rounds=ROUNDS)

    with pytest.raises(LlmError):
        _final(runner, {"question": "add 1 and 2"})
    final = _final(runner, {"question": "what was that?"})

    assert [(m.role, m.content) for m in final["messages"]][:3] == [
        ("user", "add 1 and 2"),
        ("assistant", ""),
        ("tool", "3"),
    ]


ROUTE = "route"


def test_a_step_added_to_the_walk_is_walked_in_its_place() -> None:
    """Where a turn grows: story 6 puts *route* and *focus* before the rounds, and the
    runner learns nothing — it walks the sequence it was handed."""
    walked: list[str] = []

    def routing(state: AgentState) -> AgentState:
        walked.append(ROUTE)
        return {}

    walk = _walk(_always(_replies))
    walk["before"] = (*walk["before"], Named(ROUTE, routing))
    runner = langgraph_for(**walk, max_tool_rounds=ROUNDS)
    assert isinstance(runner, LangGraphRunner)

    final = _final(runner, {"question": "q"})

    assert walked == [ROUTE]
    assert _entered(final) == [SCREEN, ROUTE, WORK, ANSWER]


def _spent(state: AgentState) -> int:
    """Rounds this turn has taken, counted as the router counts them."""
    return sum(
        1
        for message in tuple(state.get("messages", ()))[state.get("turn_start", 0) :]
        if message.role == "assistant"
    )


def _asks_then_spends(rounds: int) -> Step:
    """A turn of every superstep it is allowed: it stops to ask on its first round,
    calls a tool on each round after that, and answers on the last one it may spend."""

    def model(state: AgentState) -> AgentState:
        spent = _spent(state)
        if spent + 1 >= rounds:
            return {"messages": _said("assistant", "done")}
        if spent == 0:
            return _asks_then_answers({})
        return {"messages": _asked_for_a_tool("again")}

    return model


def _spends(rounds: int) -> Step:
    """A turn that never pauses and spends every round it has, answering on the last:
    the longest single walk of the graph, which is what the limit has to allow."""

    def model(state: AgentState) -> AgentState:
        if _spent(state) + 1 >= rounds:
            return {"messages": _said("assistant", "done")}
        return {"messages": _asked_for_a_tool("again")}

    return model


@pytest.mark.parametrize("rounds", [1, 2, 3, 8])
@pytest.mark.parametrize("grown", [(), (Named(ROUTE, _nothing),)])
def test_the_longest_walk_a_budget_allows_still_answers(
    rounds: int, grown: tuple[NamedStep, ...]
) -> None:
    """The limit is sized from the walk and spent one `run` at a time, so the longest
    single walk is what it has to be tested against: every round, and every named step
    either side of them. Walked at the sizing *minus* its declared slack, so a term left
    out of the formula fails here rather than being absorbed. A walk grown by a step is
    sized for that step too, which is what story 6 will lean on."""
    walk = _walk(_always(_spends(rounds)), rounds=rounds)
    walk["before"] = (*walk["before"], *grown)
    sized = langgraph_for(**walk, max_tool_rounds=rounds)
    assert isinstance(sized, LangGraphRunner)
    tight = replace(sized, recursion_limit=sized.recursion_limit - HEADROOM)

    assert _final(tight, {"question": "q"})["answer"] == "done"


def test_a_turn_that_asks_and_then_overspends_trips_the_core_s_limit() -> None:
    """And the other side of the same sizing: what stops a turn that will not finish is
    the round budget, whose message asks for a rephrasing, and never the graph's own
    guard, which would arrive as a `GraphRecursionError` nobody worded."""
    runner = langgraph_for(
        **_walk(
            _always(_asks_then_spends(ROUNDS + 2)),
            ask=AskStep(pause=interrupting),
            rounds=ROUNDS,
        ),
        max_tool_rounds=ROUNDS,
    )

    list(runner.run({"question": WANTED}, THREAD))

    with pytest.raises(ToolLoopLimitError) as spent:
        list(runner.resume(Answer(action="77 kg"), THREAD))

    assert spent.value.__cause__ is None


def test_a_walk_with_nothing_after_the_rounds_ends_when_they_do() -> None:
    """The port lets `after` be empty, so the loop leaves the graph rather than a step.
    That the walk still finishes is what the runner owes; that such a turn has no answer
    to give is the agent's to say, and it says so with a `GraphRunError`."""
    walk = _walk(_always(_replies))
    walk["after"] = ()
    runner = langgraph_for(**walk, max_tool_rounds=ROUNDS)
    assert isinstance(runner, LangGraphRunner)

    final = _final(runner, {"question": "q"})

    assert _entered(final) == [SCREEN, WORK]
    assert final["answer"] == "", "and nothing settled one"


def test_a_resumed_turn_writes_the_working_step_s_marker_only_once() -> None:
    """The marker is a checkpointed node's contribution, and a checkpointed node does
    not run again on the way back. Written twice, the page would show the turn entering
    the same step twice with nothing else to say it went wrong."""
    runner = _stopping()
    list(runner.run({"question": WANTED}, THREAD))

    final = list(runner.resume(Answer(action="75 kg"), THREAD))[-1]

    assert _entered(final) == [SCREEN, WORK, ANSWER]


def test_a_nested_step_survives_a_checkpoint_as_the_children_it_had() -> None:
    """A trace is a tree once a plugin's tool runs work of its own, and the thread has
    to hand that tree back: the checkpoint finds trace kinds rather than listing them,
    and a child is one of the kinds it finds."""
    nested = ToolUse(
        name="research",
        arguments={"question": "why?"},
        outcome="answered",
        steps=(ModelDecision(detail="looking", tools=("add",)), _A_STEP),
    )

    def tracing(state: AgentState) -> AgentState:
        return {"messages": _said("assistant", "ok"), "trace": [nested]}

    runner = _runner(model=_always(tracing))
    _final(runner, {"question": "first"})

    final = _final(runner, {"question": "second"})

    [replayed] = [
        step
        for step in final["trace"][:4]
        if isinstance(step, ToolUse) and step.name == "research"
    ]
    assert replayed == nested, "the same step, not one that merely reads alike"
    assert replayed.steps == (ModelDecision(detail="looking", tools=("add",)), _A_STEP)


BOOKED = "book_it"
CANCELLED = "cancel_it"
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
    """A model that asks for these effecting calls once, then answers."""

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
    """A turn whose only tools declare effects, and a list of what actually ran."""
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


def test_a_proposed_effect_parks_the_turn_before_its_tool_runs() -> None:
    """The gate stands between the model and the tools, so the call is put to the reader
    and nothing has happened while they think about it."""
    runner, ran = _gated(BOOKED)

    list(runner.run({"question": "book it"}, THREAD))
    waiting = runner.pending(THREAD)

    assert ran == [], "nothing outside cora ran while the turn waited"
    assert waiting is not None
    assert (
        waiting.card
        == Proposed(call_id="c1", tool=BOOKED, does=BOOKING, arguments={}).card
    )


def test_an_approved_effect_runs_once_and_the_turn_answers() -> None:
    runner, ran = _gated(BOOKED)
    list(runner.run({"question": "book it"}, THREAD))

    final = list(runner.resume(Answer(action="c1"), THREAD))[-1]

    assert ran == [BOOKED]
    assert final["answer"] == "done"
    assert runner.pending(THREAD) is None


def test_a_declined_effect_never_runs_and_the_turn_still_answers() -> None:
    runner, ran = _gated(BOOKED)
    list(runner.run({"question": "book it"}, THREAD))

    final = list(runner.resume(Answer(), THREAD))[-1]

    assert ran == []
    assert final["answer"] == "done"
    assert any(
        message.role == "tool" and BOOKED in message.content
        for message in final["messages"]
    ), "the model is told the call was declined, so it can answer around it"


def test_two_effects_in_one_round_are_both_settled_before_either_runs() -> None:
    """The scenario the story asks for: two stops, each naming its own call, nothing run
    at the moment the second is put — and then each running exactly once."""
    runner, ran = _gated(BOOKED, CANCELLED)

    list(runner.run({"question": "book and cancel"}, THREAD))
    first = runner.pending(THREAD)
    list(runner.resume(Answer(action="c1"), THREAD))
    second = runner.pending(THREAD)
    ran_between = list(ran)
    final = list(runner.resume(Answer(action="c2"), THREAD))[-1]

    assert first is not None and second is not None
    assert (first.card.actions[0].answer, second.card.actions[0].answer) == ("c1", "c2")
    assert ran_between == [], "settling the second is not running the first"
    assert ran == [BOOKED, CANCELLED]
    assert final["answer"] == "done"


def test_one_approved_and_one_declined_runs_only_the_one_that_was() -> None:
    runner, ran = _gated(BOOKED, CANCELLED)
    list(runner.run({"question": "book and cancel"}, THREAD))
    list(runner.resume(Answer(action="c1"), THREAD))

    final = list(runner.resume(Answer(), THREAD))[-1]

    assert ran == [BOOKED]
    told = [
        message.content
        for message in final["messages"]
        if message.role == "tool" and message.tool_call_id == "c2"
    ]
    assert told == [DECLINED_CALL.format(name=CANCELLED)], (
        "and the model hears about it"
    )


def test_a_label_arriving_at_the_gate_is_read_as_a_decline() -> None:
    """Resuming a thread parked on a proposal with a decision's answer settles nothing:
    whatever comes back is checked, and only this call's own yes is an approval."""
    runner, ran = _gated(BOOKED)
    list(runner.run({"question": "book it"}, THREAD))

    list(runner.resume(Answer(action="yes please"), THREAD))

    assert ran == []


def test_a_proposal_is_what_a_thread_is_carried_through_a_checkpoint_as() -> None:
    """Both shapes travel as data, so a page reopened while a turn is parked finds the
    proposal — a serialiser not told about them would lose the turn."""
    named = checkpointed_types()

    assert ("cora.domain.approval", "Proposed") in named
    assert ("cora.domain.card", "Card") in named
    assert ("cora.domain.card", "Answer") in named
