import logging
from collections.abc import Callable
from dataclasses import dataclass

from cora.domain.agent_state import AgentState
from cora.domain.chat_result import ChatResult
from cora.domain.citations import cited
from cora.domain.conversation import Turn
from cora.domain.errors import AdapterError, GraphRunError
from cora.domain.trace import TraceStep
from cora.ports.conversations import Conversations
from cora.ports.graph import GraphRunner

log = logging.getLogger(__name__)


def _ignore(step: TraceStep) -> None:
    pass


@dataclass(frozen=True)
class Agent:
    runner: GraphRunner
    conversations: Conversations | None = None

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
        result = ChatResult(
            answer=answer,
            citations=cited(answer, tuple(final.get("citations", ()))),
            trace=tuple(final.get("trace", ()))[started:],
        )
        self._record(thread_id, Turn(question=question, result=result))
        return result

    def _record(self, thread_id: str, turn: Turn) -> None:
        """Keeping the conversation is bookkeeping beside the answer it is about: a
        store that went away loses the record, never the reply the user asked for."""
        if self.conversations is None:
            return
        try:
            self.conversations.record(thread_id, turn)
        except AdapterError as unreachable:
            log.warning("the turn was answered but not kept: %s", unreachable)
