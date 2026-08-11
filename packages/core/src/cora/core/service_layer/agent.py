from collections.abc import Callable
from dataclasses import dataclass

from cora.core.domain.agent_state import AgentState
from cora.core.domain.citations import Source, cited_sources
from cora.core.domain.errors import AdapterError, GraphRunError
from cora.core.domain.trace import SecondLookLost, TraceStep
from cora.core.domain.turn import Turn
from cora.core.ports.graph import GraphRunner


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: tuple[Source, ...] = ()
    trace: tuple[TraceStep, ...] = ()


def _ignore(step: TraceStep) -> None:
    pass


def _still_holding_the_answer(state: AgentState) -> bool:
    """The gate is holding an answer and nothing has answered the look it took: its
    reminder is still the last thing said. A found source proves nothing either way —
    the gate does the searching, so it registers passages whether or not the model
    ever replies to them. Asked of the gate's own record, never of round counting —
    the state a run yielded last can predate the failure."""
    if "answer_in_hand" not in state:
        return False
    held = state["answer_in_hand"]
    messages = state.get("messages") or []
    unanswered = bool(messages) and messages[-1].role == "system"
    return bool(held) and state.get("answer") == held and unanswered


@dataclass(frozen=True)
class Agent:
    runner: GraphRunner

    def answer(
        self,
        question: str,
        history: tuple[Turn, ...] = (),
        on_step: Callable[[TraceStep], None] = _ignore,
    ) -> ChatResult:
        """Reports each step the moment the run takes it, so a caller can show
        the work in progress; a run that fails keeps the steps already reported.
        A failure inside the grounding gate's extra round is survivable — the run
        already had an answer, and losing it to a second look would be worse than
        an ungrounded one."""
        final: AgentState = {}
        reported = 0
        try:
            for state in self.runner.run({"question": question, "history": history}):
                final = state
                steps = state.get("trace", [])
                for step in steps[reported:]:
                    on_step(step)
                reported = len(steps)
        except AdapterError:
            if not _still_holding_the_answer(final):
                raise
            on_step(SecondLookLost())
            final = {**final, "trace": [*final.get("trace", []), SecondLookLost()]}
        if not final:
            raise GraphRunError
        answer = final.get("answer", "")
        return ChatResult(
            answer=answer,
            sources=cited_sources(answer, tuple(final.get("sources", ()))),
            trace=tuple(final.get("trace", ())),
        )
