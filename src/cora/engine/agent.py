"""The agent a frontend talks to: one turn in, one result out."""

import logging
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from cora.domain.agent_state import AgentState
from cora.domain.chat_result import ChatResult
from cora.domain.citations import cited
from cora.domain.conversation import Turn
from cora.domain.decision import Pending, TurnPaused
from cora.domain.errors import AdapterError, GraphRunError, NothingToResumeError
from cora.domain.trace import TraceStep
from cora.ports.chat_model import TextSink, unheard
from cora.ports.conversations import Conversations
from cora.ports.graph import GraphRunner

log = logging.getLogger(__name__)


def _ignore(step: TraceStep) -> None:
    pass


@dataclass(frozen=True)
class Agent:
    """What a frontend asks. Answers a turn, or stops and says what it needs settled.

    Without a `conversations` slot a turn is answered and not kept: the record is
    bookkeeping beside the answer, never a condition of it.
    """

    runner: GraphRunner
    conversations: Conversations | None = None

    def answer(
        self,
        question: str,
        thread_id: str,
        on_step: Callable[[TraceStep], None] = _ignore,
        on_text: TextSink = unheard,
    ) -> ChatResult:
        """One turn on a named thread, which is where the conversation now lives.

        The question alone is seeded, and the steps reported are this turn's — a thread
        arrives carrying every step it has ever taken. Each step is reported the moment
        the run takes it, so a caller can show the work in progress, and a run that
        fails keeps the steps already reported.

        Args:
            question: What to answer. The thread supplies everything said before it.
            thread_id: The conversation this turn belongs to. One nothing was recorded
                under starts a new one.
            on_step: Called once per step, as it is taken.
            on_text: What the model writes as it writes it, which no step reported
                between supersteps could carry: it is handed *in* to the run rather than
                read off the states coming out. Nothing about the result changes. Only
                the last round of a turn is the answer, so a round that ends in a tool
                call closes with an `Aside`.

        Returns:
            The answer, the citations it rests on, and this turn's steps.

        Raises:
            TurnPaused: The turn stopped to ask. There is no answer yet, and `resume` is
                what finishes it.
            InputRejectedError: A rule refused the question.
            AdapterError: Something outside cora failed mid-turn.
        """
        return self._turn(
            self.runner.run({"question": question}, thread_id, on_text),
            question,
            thread_id,
            on_step,
        )

    def resume(
        self,
        chosen: str | None,
        thread_id: str,
        on_step: Callable[[TraceStep], None] = _ignore,
        on_text: TextSink = unheard,
    ) -> ChatResult:
        """The rest of a turn that stopped to ask, on the label the user picked.

        Or on nothing, if they declined. The question is read off the pause rather than
        passed in, because the turn it belongs to is the one already parked on this
        thread and no caller should be able to record it under a different one.

        Raises:
            NothingToResumeError: This thread is not waiting on a decision.
        """
        waiting = self.runner.pending(thread_id)
        if waiting is None:
            raise NothingToResumeError
        return self._turn(
            self.runner.resume(chosen, thread_id, on_text),
            waiting.asked,
            thread_id,
            on_step,
        )

    def pending(self, thread_id: str) -> Pending | None:
        """What this thread is waiting on, or nothing.

        For a caller that arrived after the pause: a page reloaded while a decision was
        still open has no other way to find it, because a turn is recorded only once it
        has an answer.
        """
        return self.runner.pending(thread_id)

    def _turn(
        self,
        states: Iterator[AgentState],
        question: str,
        thread_id: str,
        on_step: Callable[[TraceStep], None],
    ) -> ChatResult:
        found: AgentState | None = None
        final: AgentState = {}
        started = reported = 0
        for state in states:
            if found is None:
                found = state
                started = reported = len(state.get("trace", ()))
                continue
            final = state
            steps = state.get("trace", [])
            for step in steps[reported:]:
                on_step(step)
            reported = len(steps)
        waiting = self.runner.pending(thread_id)
        if waiting is not None:
            raise TurnPaused(waiting)
        if not final:
            raise GraphRunError
        answer = final.get("answer", "")
        result = ChatResult(
            answer=answer,
            citations=cited(answer, tuple(final.get("citations", ()))),
            trace=tuple(final.get("trace", ()))[final.get("trace_start", started) :],
        )
        self._record(thread_id, Turn(question=question, result=result))
        return result

    def _record(self, thread_id: str, turn: Turn) -> None:
        """Keep the turn, if there is anywhere to keep it.

        Bookkeeping beside the answer it is about: a store that went away loses the
        record, never the reply the user asked for.
        """
        if self.conversations is None:
            return
        try:
            self.conversations.record(thread_id, turn)
        except AdapterError as unreachable:
            log.warning("the turn was answered but not kept: %s", unreachable)
