from collections.abc import Iterator

import pytest

from cora.domain.agent_state import AgentState
from cora.domain.citations import Source
from cora.domain.errors import GraphRunError, LlmError, ToolLoopLimitError
from cora.domain.trace import (
    ModelDecision,
    Reconsidered,
    SecondLookLost,
    ToolUse,
    TraceStep,
)
from cora.domain.turn import Turn
from cora.engine.agent import Agent
from cora.ports.chat_model import Message
from cora.ports.plugin import ToolCall

SEARCHED = ToolUse(name="search_documents", arguments={"query": "protein"})
ANSWERED = ModelDecision()
RECONSIDERED = Reconsidered()
_A_CALL = ToolCall(name="search_documents", arguments={"query": "p"}, call_id="c1")


def _held(answer: str) -> AgentState:
    """The state the gate leaves behind: the answer it is holding, the passages it
    found, and its reminder still the last thing said — nothing has answered it."""
    return {
        "answer": answer,
        "answer_in_hand": answer,
        "messages": [Message(role="system", content="weigh these")],
        "sources": [Source(1, "note.md")],
        "trace": [ANSWERED, RECONSIDERED],
        "rounds": 1,
    }


def _answered_the_gate(answer: str) -> AgentState:
    """The gate's look came back: the model replied after the reminder."""
    return {
        **_held(answer),
        "messages": [
            Message(role="system", content="weigh these"),
            Message(role="assistant", content="", tool_calls=(_A_CALL,)),
        ],
        "rounds": 2,
    }


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


def test_an_answer_already_in_hand_survives_a_failed_second_look() -> None:
    """The grounding gate makes a run that already has an answer take one more
    round. If that round dies, the user still gets the answer it had."""
    runner = _StubRunner(
        {"answer": "Hello!", "trace": [ANSWERED], "rounds": 1},
        _held("Hello!"),
        then=LlmError(),
    )

    result = Agent(runner).answer("Hi!")

    assert result.answer == "Hello!"


def test_a_failure_before_any_answer_still_travels_out() -> None:
    runner = _StubRunner({"trace": [SEARCHED]}, then=LlmError())

    with pytest.raises(LlmError):
        Agent(runner).answer("q")


def test_a_failed_first_round_is_not_rescued_by_an_unnudged_answer() -> None:
    """Only the gate's extra round is forgiven: any other failure after an answer
    would be hiding a real one."""
    runner = _StubRunner(
        {"answer": "Hello!", "trace": [ANSWERED], "rounds": 1}, then=LlmError()
    )

    with pytest.raises(LlmError):
        Agent(runner).answer("Hi!")


def test_a_failure_once_the_second_look_has_landed_is_an_ordinary_failure() -> None:
    """What tells the two apart is whether anything answered the gate, not whether a
    source turned up: the gate registers the passages it found either way."""
    runner = _StubRunner(_held("Hello!"), _answered_the_gate("Hello!"), then=LlmError())

    with pytest.raises(LlmError):
        Agent(runner).answer("Hi!")


def test_the_give_up_apology_is_never_forgiven_even_mid_second_look() -> None:
    """A verdict the router reached is not a failure to reach the model."""
    runner = _StubRunner(_held("Hello!"), then=ToolLoopLimitError())

    with pytest.raises(ToolLoopLimitError):
        Agent(runner).answer("Hi!")


def test_a_rescue_records_that_the_second_look_never_came_back() -> None:
    seen: list[TraceStep] = []
    runner = _StubRunner(_held("Hello!"), then=LlmError())

    result = Agent(runner).answer("Hi!", on_step=seen.append)

    assert isinstance(result.trace[-1], SecondLookLost)
    assert seen[-1] == result.trace[-1]


def test_a_runner_that_walks_no_step_at_all_is_a_failure_not_an_empty_answer() -> None:
    """The port promises at least one state. A runner that yields none would
    otherwise return a blank answer that reads like a successful turn."""
    with pytest.raises(GraphRunError):
        Agent(_StubRunner()).answer("q")


def test_a_run_that_fails_midway_keeps_the_steps_it_already_reported() -> None:
    seen: list[TraceStep] = []
    runner = _StubRunner({"trace": [SEARCHED]}, then=LlmError())

    with pytest.raises(LlmError):
        Agent(runner).answer("q", on_step=seen.append)

    assert seen == [SEARCHED]
