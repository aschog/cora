from collections.abc import Callable
from dataclasses import dataclass

from cora.domain.agent_state import AgentState
from cora.domain.chat_result import ChatResult
from cora.domain.citations import cited_sources
from cora.domain.errors import GraphRunError
from cora.domain.trace import TraceStep
from cora.ports.graph import GraphRunner


def _ignore(step: TraceStep) -> None:
    pass


@dataclass(frozen=True)
class Agent:
    runner: GraphRunner

    def answer(
        self,
        question: str,
        thread_id: str,
        on_step: Callable[[TraceStep], None] = _ignore,
    ) -> ChatResult:
        """One turn on a named thread, which is where the conversation now lives: the
        question alone is seeded, and the steps reported are this turn's — the thread
        arrives carrying every step it has ever taken. Each step is reported the moment
        the run takes it, so a caller can show the work in progress, and a run that
        fails keeps the steps already reported."""
        found: AgentState | None = None
        final: AgentState = {}
        started = reported = 0
        for state in self.runner.run({"question": question}, thread_id):
            if found is None:
                found = state
                started = reported = len(state.get("trace", ()))
                continue
            final = state
            steps = state.get("trace", [])
            for step in steps[reported:]:
                on_step(step)
            reported = len(steps)
        if not final:
            raise GraphRunError
        answer = final.get("answer", "")
        return ChatResult(
            answer=answer,
            sources=cited_sources(answer, tuple(final.get("sources", ()))),
            trace=tuple(final.get("trace", ()))[started:],
        )
