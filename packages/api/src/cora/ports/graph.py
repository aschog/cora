from collections.abc import Iterator
from typing import Protocol

from cora.domain.agent_state import AgentState

DONE = "done"
TOOLS = "tools"
GROUND = "ground"
"""What the router can decide, and therefore what a `GraphRunner` has to understand. It
belongs beside the port for the same reason `AgentState` marks its accumulating keys: a
graph engine is told the shape and the vocabulary, and imports nothing of the engine to
learn them."""


class GraphRunner(Protocol):
    """Drives one run of the agent's steps, yielding the state as it accumulates:
    at least one state, one per step taken, the last of them the finished run.
    Core errors raised inside a step travel out of the iteration unwrapped — and
    the state yielded last may predate such a failure, so it is no evidence about
    what the run had reached when it failed."""

    def run(self, state: AgentState) -> Iterator[AgentState]: ...
