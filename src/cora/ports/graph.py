from collections.abc import Callable, Iterator
from typing import Protocol

from cora.domain.agent_state import AgentState

DONE = "done"
TOOLS = "tools"
"""What the router can decide, and therefore what a `GraphRunner` has to understand. It
belongs beside the port for the same reason `AgentState` marks its accumulating keys: a
graph engine is told the shape and the vocabulary, and imports nothing of the engine to
learn them."""


class Step(Protocol):
    def __call__(self, state: AgentState) -> AgentState: ...


Route = Callable[[AgentState], str]


class GraphRunner(Protocol):
    """Drives one turn of the agent's steps on a named thread, yielding the state as
    it accumulates: the thread as the turn found it, then one state per step taken,
    the last of them the finished turn. A thread remembers its own conversation, so a
    second turn is seeded with the question alone. Core errors raised inside a step
    travel out of the iteration unwrapped — and the state yielded last may predate
    such a failure, so it is no evidence about what the run had reached when it
    failed."""

    def run(self, state: AgentState, thread_id: str) -> Iterator[AgentState]: ...


class GraphFor(Protocol):
    """How a composition root asks for a runner. It has the steps and the router
    already; the round budget is passed because a graph engine may need to size a limit
    of its own from it. Which engine walks them is the slot's to decide, like every
    other port — without this the graph was the one slot the wiring hard-coded."""

    def __call__(
        self,
        *,
        prepare: Step,
        model: Step,
        tools: Step,
        router: Route,
        max_tool_rounds: int,
    ) -> GraphRunner: ...
