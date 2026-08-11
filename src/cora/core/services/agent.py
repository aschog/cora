from collections.abc import Callable
from dataclasses import dataclass

from cora.core.agent_state import AgentState
from cora.core.citations import Source, cited_sources
from cora.core.errors import AdapterError, GraphRunError
from cora.core.ports.graph import GraphRunner
from cora.core.trace import SecondLookLost, TraceStep
from cora.core.turn import Turn


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: tuple[Source, ...] = ()
    trace: tuple[TraceStep, ...] = ()


def _ignore(step: TraceStep) -> None:
    pass


def _died_taking_the_second_look(state: AgentState) -> bool:
    """The gate's own extra round is the one that has not landed: the nudge
    remembers the round it interrupted, and any round completed since makes the
    failure an ordinary one, with an answer too old to stand for it. Read only
    for an `AdapterError` — the state a run yielded last can predate a failure the
    router raised, so it is no evidence about a verdict the router reached."""
    if "nudged_at" not in state:
        return False
    return state["nudged_at"] == state.get("rounds", 0) and bool(state.get("answer"))


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
            if not _died_taking_the_second_look(final):
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
