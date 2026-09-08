from collections.abc import Iterator

import pytest

from cora.domain.agent_state import AgentState
from cora.domain.card import Answer
from cora.domain.chat_result import ChatResult
from cora.domain.citations import Citation
from cora.domain.conversation import Turn
from cora.domain.decision import Decision, Option, Pending, TurnPaused
from cora.domain.errors import (
    LlmError,
)
from cora.domain.trace import ModelDecision, StepEntered, ToolUse, TraceStep
from cora.engine.agent import Agent
from cora.ports.chat_model import Piece, TextSink, unheard
from fakes import FakeConversations

SEARCHED = ToolUse(name="search_documents", arguments={"query": "protein"})
ANSWERED = ModelDecision()
THREAD = "t1"


def _at(document: str, number: int) -> Citation:
    return Citation(number=number, document=document, start=0, end=10)


class _StubRunner:
    """Yields the way a graph on a thread does: the thread as the turn found it, then
    each state a step leaves behind, accumulated."""

    def __init__(
        self,
        *states: AgentState,
        found: AgentState | None = None,
        then: Exception | None = None,
        writes: tuple[str, ...] = (),
        waiting: Pending | None = None,
        after: tuple[AgentState, ...] = (),
        pin: str | None = None,
        forgetting: Exception | None = None,
    ) -> None:
        self.forgetting = forgetting
        self.found = found or {}
        self.states = states
        self.then = then
        self.writes = writes
        self.waiting = waiting
        self.after = after
        self.pin = pin
        self.seeded: AgentState | None = None
        self.thread_id: str | None = None
        self.chosen: Answer | None = None
        self.resumes = 0
        self.forgotten: list[str] = []

    def run(
        self, state: AgentState, thread_id: str, on_text: TextSink = unheard
    ) -> Iterator[AgentState]:
        self.seeded = state
        self.thread_id = thread_id
        yield {**self.found, **state}
        for piece in self.writes:
            on_text(Piece(piece))
        yield from self.states
        if self.then is not None:
            raise self.then

    def resume(
        self, answer: Answer, thread_id: str, on_text: TextSink = unheard
    ) -> Iterator[AgentState]:
        self.chosen = answer
        self.resumes += 1
        self.thread_id = thread_id
        self.waiting = None
        yield {**self.found}
        yield from self.after

    def pending(self, thread_id: str) -> Pending | None:
        return self.waiting

    def forget(self, thread_id: str) -> None:
        if self.forgetting is not None:
            raise self.forgetting
        self.forgotten.append(thread_id)
        self.pin = None
        self.waiting = None

    def pinned(self, thread_id: str) -> str | None:
        return self.pin


def _traced(*steps: TraceStep) -> AgentState:
    return {"answer": "done", "trace": list(steps)}


def test_answer_seeds_the_run_with_the_question_and_names_the_thread() -> None:
    """The conversation is the thread's, so the question and what the turn runs under
    are all there is to seed: history left the signature with the turn that stopped
    replaying it."""
    runner = _StubRunner({"answer": "80 kg."})

    result = Agent(runner).answer("What was my weight?", "t1", scopes=("fitness",))

    assert runner.seeded == {
        "question": "What was my weight?",
        "scopes": ["fitness"],
        "pinning": "",
    }, "a turn asking for no pin says so, or the last turn's request would stand"
    assert runner.thread_id == "t1"
    assert result.answer == "80 kg."


def test_only_the_cited_passages_are_reported_under_their_own_numbers() -> None:
    registered = [_at("a.md", 1), _at("b.md", 2), _at("c.md", 3)]
    runner = _StubRunner({"answer": "Per [3] and [1].", "citations": registered})

    result = Agent(runner).answer("q", THREAD)

    assert result.citations == (_at("a.md", 1), _at("c.md", 3))


def test_every_step_is_reported_as_it_arrives() -> None:
    seen: list[str] = []
    runner = _StubRunner(
        {"trace": [SEARCHED]},
        _traced(SEARCHED, ANSWERED),
    )

    Agent(runner).answer("q", THREAD, on_step=lambda step: seen.append(step.summary))

    assert seen == [SEARCHED.summary, ANSWERED.summary]


def test_the_turn_it_took_is_recorded() -> None:
    """A conversation the reader can come back to is written where the agent is, not
    where it is drawn: every frontend gets history without keeping its own."""
    conversations = FakeConversations()
    agent = Agent(
        runner=_StubRunner({"answer": "1.6 g per kg"}), conversations=conversations
    )

    result = agent.answer("How much protein?", THREAD)

    assert conversations.turns(THREAD) == (
        Turn(question="How much protein?", result=result),
    )


def test_a_turn_that_failed_records_nothing() -> None:
    """A conversation is reopened to read what was answered; a turn that raised has no
    answer to come back to, and a list of sessions naming one is a dead end."""
    conversations = FakeConversations()
    agent = Agent(runner=_StubRunner(then=LlmError()), conversations=conversations)

    with pytest.raises(LlmError):
        agent.answer("How much protein?", THREAD)

    assert conversations.turns(THREAD) == ()


# ── a turn that stopped to ask ──

ASKED = "Which bodyweight should I treat as current?"
QUESTION = "What is my BMR?"
PARKED = Pending(
    asked=QUESTION,
    card=Decision(
        question=ASKED,
        options=(Option(label="77 kg"), Option(label="75 kg", note="February")),
        decline="Neither",
    ).card,
)


def test_a_turn_that_stopped_to_ask_says_so_rather_than_answering() -> None:
    runner = _StubRunner({"answer": ""}, waiting=PARKED)

    with pytest.raises(TurnPaused) as paused:
        Agent(runner).answer(QUESTION, THREAD)

    assert paused.value.pending == PARKED


def test_resuming_finishes_the_turn_the_pause_belonged_to() -> None:
    kept = FakeConversations()
    runner = _StubRunner(waiting=PARKED, after=({"answer": "1,730 kcal."},))

    result = Agent(runner, kept).resume(Answer(action="75 kg"), THREAD)

    assert runner.chosen == Answer(action="75 kg")
    assert result.answer == "1,730 kcal."
    [recorded] = kept.turns(THREAD)
    assert recorded == Turn(question=QUESTION, result=result), (
        "the turn is kept under the question that opened it, not under the decision"
    )


def test_a_failure_from_inside_a_step_is_named_by_the_step_the_turn_was_in() -> None:
    """A step names its own failures, but the rounds inside *work* are the loop's own
    steps and name none. Where the turn had got to is what the trace says, so that is
    what a failure out of the loop is reported under."""
    runner = _StubRunner(
        {"trace": [StepEntered("screen")]},
        {"trace": [StepEntered("screen"), StepEntered("work")]},
        then=LlmError(),
    )

    with pytest.raises(LlmError) as unreachable:
        Agent(runner).answer("q", THREAD)

    assert unreachable.value.step == "work"


def test_forgetting_a_conversation_drops_its_turns_and_its_thread() -> None:
    """One call over both halves: a conversation whose record is gone and whose thread
    is not has a pin, a transcript and possibly a parked turn nobody can see."""
    conversations = FakeConversations()
    conversations.record(
        THREAD,
        Turn(question="How much protein?", result=ChatResult(answer="1.6 g per kg.")),
    )
    runner = _StubRunner(pin="fitness")
    agent = Agent(runner=runner, conversations=conversations)

    agent.forget(THREAD)

    assert conversations.turns(THREAD) == ()
    assert runner.forgotten == [THREAD]
    assert runner.pinned(THREAD) is None
