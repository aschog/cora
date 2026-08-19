from collections.abc import Iterator

import pytest

from cora.domain.agent_state import AgentState
from cora.domain.citations import Citation
from cora.domain.conversation import Turn
from cora.domain.errors import GraphRunError, LlmError
from cora.domain.trace import ModelDecision, ToolUse, TraceStep
from cora.engine.agent import Agent
from cora.ports.chat_model import Piece, TextSink, Written, unheard
from fakes import FailingConversations, FakeConversations

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
    ) -> None:
        self.found = found or {}
        self.states = states
        self.then = then
        self.writes = writes
        self.seeded: AgentState | None = None
        self.thread_id: str | None = None

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


def _traced(*steps: TraceStep) -> AgentState:
    return {"answer": "done", "trace": list(steps)}


def test_answer_seeds_the_run_with_the_question_and_names_the_thread() -> None:
    """The conversation is the thread's, so there is nothing else to seed: history
    left the signature with the turn that stopped replaying it."""
    runner = _StubRunner({"answer": "80 kg."})

    result = Agent(runner).answer("What was my weight?", "t1")

    assert runner.seeded == {"question": "What was my weight?"}
    assert runner.thread_id == "t1"
    assert result.answer == "80 kg."


def test_only_the_cited_passages_are_reported_under_their_own_numbers() -> None:
    registered = [_at("a.md", 1), _at("b.md", 2), _at("c.md", 3)]
    runner = _StubRunner({"answer": "Per [3] and [1].", "citations": registered})

    result = Agent(runner).answer("q", THREAD)

    assert result.citations == (_at("a.md", 1), _at("c.md", 3))


def test_the_runs_steps_come_back_in_order() -> None:
    runner = _StubRunner(_traced(SEARCHED, ANSWERED))

    result = Agent(runner).answer("q", THREAD)

    assert result.trace == (SEARCHED, ANSWERED)


def test_every_step_is_reported_as_it_arrives() -> None:
    seen: list[str] = []
    runner = _StubRunner(
        {"trace": [SEARCHED]},
        _traced(SEARCHED, ANSWERED),
    )

    Agent(runner).answer("q", THREAD, on_step=lambda step: seen.append(step.summary))

    assert seen == [SEARCHED.summary, ANSWERED.summary]


def test_a_step_already_reported_is_never_reported_twice() -> None:
    seen: list[TraceStep] = []
    runner = _StubRunner(
        {"trace": [SEARCHED]},
        {"trace": [SEARCHED]},
        _traced(SEARCHED, ANSWERED),
    )

    Agent(runner).answer("q", THREAD, on_step=seen.append)

    assert seen == [SEARCHED, ANSWERED]


def test_a_failure_before_any_answer_still_travels_out() -> None:
    runner = _StubRunner({"trace": [SEARCHED]}, then=LlmError())

    with pytest.raises(LlmError):
        Agent(runner).answer("q", THREAD)


def test_a_failure_after_an_answer_travels_out_the_same_way() -> None:
    """An answer in the state is no reason to swallow what came after it: nothing is
    held back, so every adapter failure is the turn's failure."""
    runner = _StubRunner({"answer": "Hello!", "trace": [ANSWERED]}, then=LlmError())

    with pytest.raises(LlmError):
        Agent(runner).answer("Hi!", THREAD)


def test_a_runner_that_walks_no_step_at_all_is_a_failure_not_an_empty_answer() -> None:
    """The port promises at least one state. A runner that yields none would
    otherwise return a blank answer that reads like a successful turn."""
    with pytest.raises(GraphRunError):
        Agent(_StubRunner()).answer("q", THREAD)


def test_a_run_that_fails_midway_keeps_the_steps_it_already_reported() -> None:
    seen: list[TraceStep] = []
    runner = _StubRunner({"trace": [SEARCHED]}, then=LlmError())

    with pytest.raises(LlmError):
        Agent(runner).answer("q", THREAD, on_step=seen.append)

    assert seen == [SEARCHED]


def test_only_this_turns_steps_are_reported_and_returned() -> None:
    """The thread arrives carrying every step of every earlier turn; replaying them
    would show the user work this turn never did."""
    seen: list[TraceStep] = []
    runner = _StubRunner(
        {"trace": [SEARCHED, ANSWERED, SEARCHED]},
        {"trace": [SEARCHED, ANSWERED, SEARCHED, ANSWERED], "answer": "done"},
        found={"trace": [SEARCHED, ANSWERED]},
    )

    result = Agent(runner).answer("q", THREAD, on_step=seen.append)

    assert seen == [SEARCHED, ANSWERED]
    assert result.trace == (SEARCHED, ANSWERED)


def test_the_citations_resolve_against_the_whole_conversations_registry() -> None:
    """Numbering runs the length of the thread, so an answer citing [3] means the
    third passage the conversation registered — whichever turn found it."""
    earlier = [_at("a.md", 1), _at("b.md", 2)]
    runner = _StubRunner(
        {"answer": "As [1] and [3] say.", "citations": [*earlier, _at("c.md", 3)]},
        found={"citations": earlier},
    )

    result = Agent(runner).answer("q", THREAD)

    assert result.citations == (_at("a.md", 1), _at("c.md", 3))


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


def test_an_agent_wired_to_no_store_still_answers() -> None:
    agent = Agent(runner=_StubRunner({"answer": "1.6 g per kg"}))

    assert agent.answer("How much protein?", THREAD).answer == "1.6 g per kg"


def test_a_store_that_cannot_be_written_costs_the_turn_nothing() -> None:
    """The answer is what the user asked for; keeping a record of it is bookkeeping.
    A store that went away loses the conversation, never the reply."""
    agent = Agent(
        runner=_StubRunner({"answer": "1.6 g per kg"}),
        conversations=FailingConversations(),
    )

    assert agent.answer("How much protein?", THREAD).answer == "1.6 g per kg"


def test_the_answer_reaches_its_reader_as_it_is_written() -> None:
    """The pieces are the same text arriving earlier. What the turn *is* — recorded,
    prompted from, cited against — is still the whole answer in the result."""
    written: list[Written] = []
    runner = _StubRunner(
        {"answer": "Sleep, not volume."}, writes=("Sleep, ", "not volume.")
    )

    result = Agent(runner).answer("why", THREAD, on_text=written.append)

    assert written == [Piece("Sleep, "), Piece("not volume.")]
    assert result.answer == "Sleep, not volume."


def test_a_caller_that_reads_along_with_nothing_gets_the_same_turn() -> None:
    """Every frontend but the page asks for a turn and waits for it."""
    runner = _StubRunner({"answer": "Sleep, not volume."}, writes=("Sleep, ",))

    assert Agent(runner).answer("why", THREAD).answer == "Sleep, not volume."


def test_a_turn_that_fails_keeps_the_text_already_written() -> None:
    """As it already keeps the steps it took: what was written happened, and the caller
    replaces it with the sentence the failure carries rather than pretending to unsay
    it."""
    written: list[Written] = []
    runner = _StubRunner({"trace": [SEARCHED]}, writes=("Sleep, ",), then=LlmError())

    with pytest.raises(LlmError):
        Agent(runner).answer("why", THREAD, on_text=written.append)

    assert written == [Piece("Sleep, ")]
