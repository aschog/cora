from collections.abc import Iterator

import pytest

from cora.core.agent_state import AgentState
from cora.core.citations import Source
from cora.core.errors import LlmError
from cora.core.services.agent import Agent
from cora.core.trace import ModelDecision, ToolUse, TraceStep
from cora.core.turn import Turn

SEARCHED = ToolUse(name="search_documents", arguments={"query": "protein"})
ANSWERED = ModelDecision()


class _StubRunner:
    """Yields each state the way a graph would: accumulated, one per step."""

    def __init__(self, *states: AgentState, then: Exception | None = None) -> None:
        self.states = states
        self.then = then
        self.seeded: AgentState | None = None

    def run(self, state: AgentState) -> Iterator[AgentState]:
        self.seeded = state
        yield from self.states
        if self.then is not None:
            raise self.then


def _traced(*steps: TraceStep) -> AgentState:
    return {"answer": "done", "trace": list(steps)}


def test_answer_seeds_the_run_from_the_question_and_history() -> None:
    history = (Turn(role="user", text="I weigh 80 kg."),)
    runner = _StubRunner({"answer": "80 kg."})

    result = Agent(runner).answer("What was my weight?", history)

    assert runner.seeded == {"question": "What was my weight?", "history": history}
    assert result.answer == "80 kg."


def test_only_the_cited_sources_are_reported_under_their_own_numbers() -> None:
    registered = [Source(1, "a.md"), Source(2, "b.md"), Source(3, "c.md")]
    runner = _StubRunner({"answer": "Per [3] and [1].", "sources": registered})

    result = Agent(runner).answer("q")

    assert result.sources == (Source(1, "a.md"), Source(3, "c.md"))


def test_the_runs_steps_come_back_in_order() -> None:
    runner = _StubRunner(_traced(SEARCHED, ANSWERED))

    result = Agent(runner).answer("q")

    assert result.trace == (SEARCHED, ANSWERED)


def test_every_step_is_reported_as_it_arrives() -> None:
    seen: list[str] = []
    runner = _StubRunner(
        {"trace": [SEARCHED]},
        _traced(SEARCHED, ANSWERED),
    )

    Agent(runner).answer("q", on_step=lambda step: seen.append(step.summary))

    assert seen == [SEARCHED.summary, ANSWERED.summary]


def test_a_step_already_reported_is_never_reported_twice() -> None:
    seen: list[TraceStep] = []
    runner = _StubRunner(
        {"trace": [SEARCHED]},
        {"trace": [SEARCHED]},
        _traced(SEARCHED, ANSWERED),
    )

    Agent(runner).answer("q", on_step=seen.append)

    assert seen == [SEARCHED, ANSWERED]


def test_a_run_that_fails_midway_keeps_the_steps_it_already_reported() -> None:
    seen: list[TraceStep] = []
    runner = _StubRunner({"trace": [SEARCHED]}, then=LlmError())

    with pytest.raises(LlmError):
        Agent(runner).answer("q", on_step=seen.append)

    assert seen == [SEARCHED]
