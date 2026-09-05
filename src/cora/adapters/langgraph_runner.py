import pathlib
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from cora.domain.agent_state import AgentState
from cora.domain.card import Answer, Asks
from cora.domain.decision import Pending
from cora.domain.errors import NothingToResumeError, ToolLoopLimitError
from cora.domain.trace import step_kinds
from cora.ports.chat_model import TextSink, unheard
from cora.ports.graph import (
    ASK,
    DONE,
    TOOLS,
    GraphRunner,
    Loop,
    NamedStep,
    Settled,
)

MODEL = "model"
GATE = "gate"
"""The two nodes of a round that are not the tools. Named here rather than in
`cora.ports.graph`: the router's vocabulary is what a graph engine is told, and these
are where this engine put the steps it was handed."""
SUPERSTEPS_PER_ROUND = 3
HEADROOM = 2
"""Supersteps to spare, over the limit the longest walk of a turn was measured to need.

The limit is spent one `run` at a time, so the longest walk is a turn that never pauses
and spends every round: each named step once, then a model call, the gate and the tools
per round. The gate costs a superstep on every round whether or not it stops anything,
which is what a path that cannot be skipped costs.

The limit such a walk needs is `SUPERSTEPS_PER_ROUND * rounds + steps`, one more than
it spends, measured across budgets 1 to 12 and grown walks. The test walks it at the
sizing *minus* this slack, which is that measured limit exactly, so every term of the
formula is pinned from below and only the slack is free. Slack at all because how
LangGraph counts a superstep is its business rather than a contract, and the cost of
being one out is a legitimate turn reported as a runaway one. A pause cannot be the
longest walk: it ends the run it was in, and the resumed one pays for none of the steps
before the loop."""
CHECKPOINTED_DATA = (
    ("cora.ports.chat_model", "Message"),
    ("cora.ports.plugin", "ToolCall"),
    ("cora.domain.citations", "Citation"),
    ("cora.domain.decision", "Decision"),
    ("cora.domain.decision", "Option"),
    ("cora.domain.approval", "Proposed"),
    ("cora.domain.card", "Card"),
    ("cora.domain.card", "FieldAsked"),
    ("cora.domain.card", "ActionOffered"),
    ("cora.domain.card", "Answer"),
)
"""What a thread's state is made of besides its trace. Named because the alternative is
LangGraph's default — deserialise anything and log a warning saying it will be blocked
one day — which would make a lock bump the thing that breaks conversations, silently: a
logged warning is invisible to a test suite."""


def checkpointed_types() -> tuple[tuple[str, str], ...]:
    return (
        *CHECKPOINTED_DATA,
        *((kind.__module__, kind.__name__) for kind in step_kinds()),
    )


def _serde() -> JsonPlusSerializer:
    return JsonPlusSerializer(allowed_msgpack_modules=checkpointed_types())


def _saver() -> InMemorySaver:
    return InMemorySaver(serde=_serde())


def _saver_at(path: str) -> SqliteSaver:
    """Beside the turns the reader comes back to, in the same file: what the model was
    told and what the page redraws are two halves of one conversation, and a deployment
    that deletes the file should lose both or neither."""
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    saver = SqliteSaver(connection, serde=_serde())
    saver.setup()
    return saver


def recursion_limit_for(max_tool_rounds: int, steps: int) -> int:
    """Wide enough that the core's round budget always trips first.

    Each named step outside the rounds costs a superstep of its own, and each round
    costs a model call and its tools. `HEADROOM` says what is left over.

    Args:
        max_tool_rounds: How many rounds of tools a turn may spend.
        steps: How many named steps the turn walks besides the rounds.
    """
    return SUPERSTEPS_PER_ROUND * max_tool_rounds + steps + HEADROOM


def interrupting(asks: Asks) -> Answer | None:
    """The engine's `Answered`, bound to LangGraph's: the run is parked in the
    checkpointer carrying what it stopped on, and what the reader did arrives here when
    someone picks it up.

    Called once per card, so a node putting two of them parks twice and the answers come
    back in the order they were asked — LangGraph counts the interrupts of a task and
    replays the ones already settled. Anything back that is not an answer is nothing,
    and every step reads nothing as a decline.
    """
    answered = interrupt(asks)
    return answered if isinstance(answered, Answer) else None


@dataclass(frozen=True)
class LangGraphRunner:
    """The checkpointer is the runner's own: which technology remembers a thread is a
    binding, not something the core asks for. In memory it holds a thread for as long as
    the process runs, which is all a conversation needed while none could be reopened;
    a deployment that names a file gets one that outlives the process, so a question
    asked on a resumed thread is asked of a model that saw the exchange before it."""

    before: tuple[NamedStep, ...]
    loop: Loop
    after: tuple[NamedStep, ...]
    recursion_limit: int
    checkpointer: BaseCheckpointSaver = field(default_factory=_saver)

    def run(
        self, state: AgentState, thread_id: str, on_text: TextSink = unheard
    ) -> Iterator[AgentState]:
        yield from self._streamed(state, thread_id, on_text)

    def resume(
        self, answer: Settled, thread_id: str, on_text: TextSink = unheard
    ) -> Iterator[AgentState]:
        """The parked run, picked up where it stopped. The step that stopped is replayed
        from its first line with `interrupt` returning the answer this time, which is
        why nothing that has run may sit in front of it — and why the gate runs no tool
        of its own."""
        if self.pending(thread_id) is None:
            raise NothingToResumeError
        yield from self._streamed(Command(resume=answer), thread_id, on_text)

    def pending(self, thread_id: str) -> Pending | None:
        """What the thread is waiting on, read off the checkpoint rather than the
        stream: a run that parks simply stops yielding, so the pause is not something a
        caller can see go past.

        Whatever shape stopped it, because every one of them has a card — and the first
        outstanding interrupt is the one being answered, since a node puts its next card
        only once the one before it came back."""
        parked = self._graph(unheard).get_state(self._config(thread_id))
        waiting = next(
            (
                found.value
                for found in parked.interrupts
                if isinstance(found.value, Asks)
            ),
            None,
        )
        if waiting is None:
            return None
        return Pending(asked=parked.values.get("question", ""), card=waiting.card)

    def pinned(self, thread_id: str) -> str | None:
        """The thread's pin, read straight off the checkpointer.

        Asked of the saver rather than of a graph: `_graph` is built per run so that the
        model node can be that turn's, and a read of one key needs none of that — a turn
        carrying a pin would otherwise compile the whole walk twice before it began. A
        thread nobody has asked anything on has no checkpoint, and so no pin.
        """
        saved = self.checkpointer.get(self._config(thread_id))
        held = (saved or {}).get("channel_values", {}).get("pin")
        return held or None

    def forget(self, thread_id: str) -> None:
        """The thread dropped through the checkpointer's own delete, which every saver
        answers: what a checkpoint is made of is LangGraph's business, and cora writing
        sql against its tables would be cora holding a shape it was not given."""
        self.checkpointer.delete_thread(thread_id)

    def _streamed(
        self, opening: Any, thread_id: str, on_text: TextSink
    ) -> Iterator[AgentState]:
        try:
            yield from self._graph(on_text).stream(
                opening, self._config(thread_id), stream_mode="values"
            )
        except GraphRecursionError as exhausted:
            raise ToolLoopLimitError from exhausted

    def _config(self, thread_id: str) -> RunnableConfig:
        return {
            "recursion_limit": self.recursion_limit,
            "configurable": {"thread_id": thread_id},
        }

    def _graph(self, on_text: TextSink) -> Any:
        """Built per run, which is what lets the model node be this turn's: the sink
        belongs to the reader waiting on it, and a graph shared between turns could
        only hold one of them.

        The walk is the sequence it was handed, so a turn that grew a step is a graph
        with a node more and this method unchanged. The rounds are the one part of it
        with a shape of their own: the model decides, and the router sends the turn to
        the gate, to the reader, or on to whatever the walk does next. Every path to the
        tools runs through the gate — the round's route arrives there and so does the
        ask's, which is what makes the gate unbypassable by construction rather than by
        anyone remembering to call it.
        """
        # ty does not see __required_keys__ on a TypedDict class, so it cannot
        # tell that AgentState satisfies LangGraph's state-schema bound.
        builder = StateGraph(AgentState)  # ty: ignore[invalid-argument-type]
        walked = (*self.before, self.loop.marker, *self.after)
        for step in walked:
            builder.add_node(step.step, step)
        builder.add_node(MODEL, self.loop.model(on_text))
        builder.add_node(GATE, self.loop.gate)
        builder.add_node(TOOLS, self.loop.tools)
        builder.add_node(ASK, self.loop.ask)
        opening = (*self.before, self.loop.marker)
        builder.add_edge(START, opening[0].step)
        for here, there in pairwise(opening):
            builder.add_edge(here.step, there.step)
        builder.add_edge(self.loop.marker.step, MODEL)
        builder.add_conditional_edges(
            MODEL, self.loop.router, {DONE: self._done, TOOLS: GATE, ASK: ASK}
        )
        builder.add_edge(ASK, GATE)
        builder.add_edge(GATE, TOOLS)
        builder.add_edge(TOOLS, MODEL)
        for here, there in pairwise(self.after):
            builder.add_edge(here.step, there.step)
        if self.after:
            builder.add_edge(self.after[-1].step, END)
        return builder.compile(checkpointer=self.checkpointer)

    @property
    def _done(self) -> str:
        """Where a turn goes when the rounds are over: on with the walk, or out."""
        return self.after[0].step if self.after else END


def langgraph_for(
    *,
    before: tuple[NamedStep, ...],
    loop: Loop,
    after: tuple[NamedStep, ...],
    max_tool_rounds: int,
    checkpoints_at: str | None = None,
) -> GraphRunner:
    """`checkpoints_at` is this binding's own, not the `GraphFor` port's: where a thread
    is kept is a fact about LangGraph and sqlite, and a composition root binds it here
    rather than the port learning that threads live in files."""
    return LangGraphRunner(
        before=before,
        loop=loop,
        after=after,
        recursion_limit=recursion_limit_for(
            max_tool_rounds, steps=len(before) + len(after) + 1
        ),
        checkpointer=_saver() if checkpoints_at is None else _saver_at(checkpoints_at),
    )
