from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, Protocol

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph

from cora.domain.agent_state import AgentState
from cora.domain.errors import ToolLoopLimitError
from cora.ports.graph import DONE, GROUND, TOOLS

PREPARE = "prepare"
MODEL = "model"
SUPERSTEPS_PER_ROUND = 2


class Step(Protocol):
    def __call__(self, state: AgentState) -> AgentState: ...


def recursion_limit_for(max_tool_rounds: int) -> int:
    """Wide enough that the core's round budget always trips first: preparing
    costs one superstep, then each round costs a model call and its tools. The
    grounding gate needs no allowance of its own — its nudge takes the superstep
    the round it interrupts would have spent on tools."""
    return SUPERSTEPS_PER_ROUND * max_tool_rounds + 2


@dataclass(frozen=True)
class LangGraphRunner:
    prepare: Step
    model: Step
    tools: Step
    ground: Step
    router: Callable[[AgentState], str]
    recursion_limit: int

    def run(self, state: AgentState) -> Iterator[AgentState]:
        try:
            yield from self._graph().stream(
                state,
                {"recursion_limit": self.recursion_limit},
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
        return builder.compile()
