import pathlib
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph

from cora.domain.agent_state import AgentState
from cora.domain.errors import ToolLoopLimitError
from cora.domain.trace import step_kinds
from cora.ports.graph import DONE, TOOLS, GraphRunner, Route, Step

PREPARE = "prepare"
MODEL = "model"
SUPERSTEPS_PER_ROUND = 2
CHECKPOINTED_DATA = (
    ("cora.ports.chat_model", "Message"),
    ("cora.ports.plugin", "ToolCall"),
    ("cora.domain.citations", "Citation"),
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


def recursion_limit_for(max_tool_rounds: int) -> int:
    """Wide enough that the core's round budget always trips first: preparing
    costs one superstep, then each round costs a model call and its tools."""
    return SUPERSTEPS_PER_ROUND * max_tool_rounds + 2


@dataclass(frozen=True)
class LangGraphRunner:
    """The checkpointer is the runner's own: which technology remembers a thread is a
    binding, not something the core asks for. In memory it holds a thread for as long as
    the process runs, which is all a conversation needed while none could be reopened;
    a deployment that names a file gets one that outlives the process, so a question
    asked on a resumed thread is asked of a model that saw the exchange before it."""

    prepare: Step
    model: Step
    tools: Step
    router: Route
    recursion_limit: int
    checkpointer: BaseCheckpointSaver = field(default_factory=_saver)

    def run(self, state: AgentState, thread_id: str) -> Iterator[AgentState]:
        try:
            yield from self._graph().stream(
                state,
                {
                    "recursion_limit": self.recursion_limit,
                    "configurable": {"thread_id": thread_id},
                },
                stream_mode="values",
            )
        except GraphRecursionError as exhausted:
            raise ToolLoopLimitError from exhausted

    def _graph(self) -> Any:
        # ty does not see __required_keys__ on a TypedDict class, so it cannot
        # tell that AgentState satisfies LangGraph's state-schema bound.
        builder = StateGraph(AgentState)  # ty: ignore[invalid-argument-type]
        builder.add_node(PREPARE, self.prepare)
        builder.add_node(MODEL, self.model)
        builder.add_node(TOOLS, self.tools)
        builder.add_edge(START, PREPARE)
        builder.add_edge(PREPARE, MODEL)
        builder.add_conditional_edges(MODEL, self.router, {DONE: END, TOOLS: TOOLS})
        builder.add_edge(TOOLS, MODEL)
        return builder.compile(checkpointer=self.checkpointer)


def langgraph_for(
    *,
    prepare: Step,
    model: Step,
    tools: Step,
    router: Route,
    max_tool_rounds: int,
    checkpoints_at: str | None = None,
) -> GraphRunner:
    """`checkpoints_at` is this binding's own, not the `GraphFor` port's: where a thread
    is kept is a fact about LangGraph and sqlite, and a composition root binds it here
    rather than the port learning that threads live in files."""
    return LangGraphRunner(
        prepare=prepare,
        model=model,
        tools=tools,
        router=router,
        recursion_limit=recursion_limit_for(max_tool_rounds),
        checkpointer=_saver() if checkpoints_at is None else _saver_at(checkpoints_at),
    )
