from typing import Protocol

from cora.core.agent_state import AgentState


class GraphRunner(Protocol):
    """Drives one run of the agent's steps to completion. Core errors raised
    inside a step travel out unwrapped."""

    def run(self, state: AgentState) -> AgentState: ...
