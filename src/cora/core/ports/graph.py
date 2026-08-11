from collections.abc import Iterator
from typing import Protocol

from cora.core.agent_state import AgentState


class GraphRunner(Protocol):
    """Drives one run of the agent's steps, yielding the state as it accumulates:
    at least one state, one per step taken, the last of them the finished run.
    Core errors raised inside a step travel out of the iteration unwrapped — and
    the state yielded last may predate such a failure, so it is no evidence about
    what the run had reached when it failed."""

    def run(self, state: AgentState) -> Iterator[AgentState]: ...
