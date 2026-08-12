from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph

from cora.domain.agent_state import AgentState
from cora.domain.errors import ToolLoopLimitError
from cora.ports.graph import DONE, GROUND, TOOLS, GraphRunner, Route, Step

PREPARE = "prepare"
MODEL = "model"
SUPERSTEPS_PER_ROUND = 2


def recursion_limit_for(max_tool_rounds: int) -> int:
    """Wide enough that the core's round budget always trips first: preparing
    costs one superstep, then each round costs a model call and its tools. The
    grounding gate needs no allowance of its own — its nudge takes the superstep
    the round it interrupts would have spent on tools."""
    return SUPERSTEPS_PER_ROUND * max_tool_rounds + 2


@dataclass(frozen=True)
class LangGraphRunner:
    """The checkpointer is the runner's own: which technology remembers a thread is a
    binding, not something the core asks for. It is in memory because a thread is one
    sitting at the app — what has to outlive the process is what the agent was told
    about the user, and that lives behind the memory port."""

    prepare: Step
    model: Step
    tools: Step
    ground: Step
    router: Route
    recursion_limit: int
    checkpointer: InMemorySaver = field(default_factory=InMemorySaver)

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
        builder.add_node(GROUND, self.ground)
        builder.add_edge(START, PREPARE)
        builder.add_edge(PREPARE, MODEL)
        builder.add_conditional_edges(
            MODEL, self.router, {DONE: END, TOOLS: TOOLS, GROUND: GROUND}
        )
        builder.add_edge(TOOLS, MODEL)
        builder.add_edge(GROUND, MODEL)
        return builder.compile(checkpointer=self.checkpointer)


def langgraph_for(
    *,
    prepare: Step,
    model: Step,
    tools: Step,
    ground: Step,
    router: Route,
    max_tool_rounds: int,
) -> GraphRunner:
    return LangGraphRunner(
        prepare=prepare,
        model=model,
        tools=tools,
        ground=ground,
        router=router,
        recursion_limit=recursion_limit_for(max_tool_rounds),
    )
