"""The agent a frontend talks to: one turn in, one result out."""

import logging
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from cora.domain.agent_state import AgentState
from cora.domain.card import Answer
from cora.domain.chat_result import ChatResult
from cora.domain.citations import cited
from cora.domain.conversation import Turn
from cora.domain.decision import Pending, TurnPaused
from cora.domain.errors import (
    AdapterError,
    CoreError,
    GraphRunError,
    NothingToResumeError,
    ScopePinnedError,
)
from cora.domain.trace import StepEntered, TraceStep
from cora.ports.chat_model import TextSink, unheard
from cora.ports.conversations import Conversations
from cora.ports.graph import GraphRunner

log = logging.getLogger(__name__)


def _ignore(step: TraceStep) -> None:
    pass


def _entered(steps: list[TraceStep]) -> str:
    """The step the turn had reached, read off the markers in its trace.

    A step names the failures raised inside it, but the rounds of the loop are steps
    of their own and name none. Where the turn had got to is what the trace says, and
    it is how a failure out of the loop is reported under the step containing it.
    """
    return next(
        (step.step for step in reversed(steps) if isinstance(step, StepEntered)), ""
    )


@dataclass(frozen=True)
class Agent:
    """What a frontend asks. Answers a turn, or stops and says what it needs settled.

    Without a `conversations` slot a turn is answered and not kept: the record is
    bookkeeping beside the answer, never a condition of it.

    What a turn runs under is the turn's own business rather than this class's: the
    routing step settles it from the conversation's pin, the caller's own scopes or the
    question itself. All this holds is the one rule about a pin that has to stand
    before a turn is started — that it is never moved.
    """

    runner: GraphRunner
    conversations: Conversations | None = None

    def answer(
        self,
        question: str,
        thread_id: str,
        on_step: Callable[[TraceStep], None] = _ignore,
        on_text: TextSink = unheard,
        scopes: tuple[str, ...] = (),
        pin: str | None = None,
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
            scopes: What this turn runs under — which of the plugins' scoped
                registrations apply to it. Given none, the turn routes itself.
            pin: The scope to fix this conversation to, from this turn on — taken once
                the question has been admitted, so a refused one fixes nothing. Sent
                again on every later turn by a caller that holds one; the same one costs
                nothing, and a different one is refused.

        Returns:
            The answer, the citations it rests on, and this turn's steps.

        Raises:
            TurnPaused: The turn stopped to ask. There is no answer yet, and `resume` is
                what finishes it.
            InputRejectedError: A rule refused the question.
            ScopePinnedError: This conversation is already pinned to another scope.
            GraphRunError: The walk came back with no answer to give.
            AdapterError: Something outside cora failed mid-turn. A failure raised
                inside a step carries that step's name.
        """
        # `pinning` is asked for rather than set: the seeded keys are written before the
        # first step runs, and a question the screen refuses must fix nothing. The step
        # that reads the pin is the step that writes it, one step further on. Written on
        # every turn, because a request is one turn's: left standing, a pin a refused
        # question asked for would be taken by whatever was asked next.
        seeded: AgentState = {
            "question": question,
            "scopes": list(scopes),
            "pinning": pin or "",
        }
        if pin is not None:
            held = self.pinned(thread_id)
            if held is not None and held != pin:
                raise ScopePinnedError(held)
        return self._turn(
            self.runner.run(seeded, thread_id, on_text), question, thread_id, on_step
        )

    def resume(
        self,
        answer: Answer,
        thread_id: str,
        on_step: Callable[[TraceStep], None] = _ignore,
        on_text: TextSink = unheard,
    ) -> ChatResult:
        """The rest of a turn that stopped, on the action the user took.

        The answer carries whatever the card it settles needs: the option picked, the
        id of the call approved, the values filled in. Whether it settles the card that
        was actually put is the stopping step's to check — an answer arrives from
        outside the run, and anything that does not fit the card is a decline.

        The question is read off the pause rather than passed in, because the turn it
        belongs to is the one already parked on this thread and no caller should be able
        to record it under a different one.

        Raises:
            NothingToResumeError: This thread is not waiting on anything.
            TurnPaused: The rest of the turn stopped again — a round proposing a second
                effect stops for that one too.
            GraphRunError: The walk came back with no answer to give.
            AdapterError: As in `answer` — the rest of a turn fails the same ways.
        """
        waiting = self.runner.pending(thread_id)
        if waiting is None:
            raise NothingToResumeError
        return self._turn(
            self.runner.resume(answer, thread_id, on_text),
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

    def forget(self, thread_id: str) -> None:
        """Delete a conversation: its turns, and the thread they were answered on.

        Both halves through one call, because a conversation whose record is gone and
        whose thread is not still holds a pin, what the model was told, and possibly a
        turn parked mid-question — reachable, and listed nowhere. The thread goes first,
        so a failure halfway leaves the conversation listed and deletable again rather
        than kept where nobody can find it. A cora with no place to record turns has
        only the thread to drop.

        Raises:
            ConversationStoreError: The turns could not be dropped.
        """
        self.runner.forget(thread_id)
        if self.conversations is not None:
            self.conversations.forget(thread_id)

    def pinned(self, thread_id: str) -> str | None:
        """The scope this conversation was fixed to, or nothing.

        What a page reopening a thread draws before anything is asked on it, and what
        makes a second pin refusable rather than silently ignored. Read before the turn
        rather than inside it, which assumes one caller per thread: cora runs on the
        machine of the person whose conversations it holds, and nothing under this
        offers the per-thread serialisation a stronger promise would need.
        """
        return self.runner.pinned(thread_id)

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
        where = ""
        try:
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
                where = _entered(steps) or where
        except CoreError as failed:
            failed.step = failed.step or where
            raise
        # Whatever follows is the turn's own judgement of the walk rather than a step's,
        # so it is raised out here, under no step's name.
        waiting = self.runner.pending(thread_id)
        if waiting is not None:
            raise TurnPaused(waiting)
        answer = final.get("answer", "")
        if not answer.strip():
            raise GraphRunError
        result = ChatResult(
            answer=answer,
            citations=cited(answer, tuple(final.get("citations", ()))),
            trace=tuple(final.get("trace", ()))[final.get("trace_start", started) :],
            scopes=tuple(final.get("scopes", ())),
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
