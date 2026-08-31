"""What a conversation is, now that the thread holds it: numbering that runs its
length, and a budget that does not."""

import pytest

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.domain.chunk import Chunk
from cora.domain.citations import CitableHits
from cora.domain.errors import ToolLoopLimitError
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.engine.steps import NO_FIELD_LOADED
from cora.ports.chat_model import ChatModel, Message, ModelReply, TextSink, unheard
from cora.ports.host import DEFAULT_SCOPE
from cora.ports.plugin import Tool, ToolCall
from cora.ports.retrieval import RetrievedChunk
from fakes import ScriptedChatModel
from fixture_plugins import make_plugin

THREAD = "t1"
PROTEIN = ("protein.md", b"aim for 1.6 g of protein per kg")
CREATINE = ("creatine.md", b"5 g of creatine daily is the usual dose")


def _searching(call_id: str, query: str = "protein") -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(
                name=SEARCH_TOOL_NAME, arguments={"query": query}, call_id=call_id
            ),
        )
    )


LOOKUP = "lookup"


def _lookup_tool() -> Tool:
    """A tool that cites the document it is asked for. The shipped search ranks
    hashed vectors in the unit fakes, so which document comes back is not a test's
    to know — and numbering is what these tests are about, not retrieval."""

    def look(name: str) -> CitableHits:
        chunk = Chunk(text=f"what {name} says", source=name, index=0, offset=0)
        return CitableHits([RetrievedChunk(chunk=chunk, score=1.0)])

    return Tool(
        name=LOOKUP,
        description="Look a document up by name.",
        parameter_schema={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
        run=look,
    )


def _looking(call_id: str, name: str) -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name=LOOKUP, arguments={"name": name}, call_id=call_id),)
    )


def _app(chat_model: ChatModel, *, rounds: int = 8) -> App:
    return indexed(
        assembled(
            chat_model=chat_model,
            plugin=make_plugin(tools=(_lookup_tool(),)),
            max_tool_rounds=rounds,
        ),
        PROTEIN,
        CREATINE,
    )


@pytest.mark.integration
def test_a_later_turn_continues_the_conversations_numbering() -> None:
    """`[1]` named one document last turn and would name another this turn, so a
    model paraphrasing its own earlier answer cited the wrong source."""
    model = ScriptedChatModel(
        [
            _looking("c1", "protein.md"),
            ModelReply(text="1.6 g per kg [1]."),
            _looking("c2", "creatine.md"),
            ModelReply(text="5 g daily [2]."),
        ]
    )
    app = _app(model)

    first = app.agent.answer("How much protein?", THREAD)
    second = app.agent.answer("And creatine?", THREAD)

    assert [(c.number, c.document) for c in first.citations] == [(1, "protein.md")]
    assert [(c.number, c.document) for c in second.citations] == [(2, "creatine.md")]


@pytest.mark.integration
def test_a_source_found_again_keeps_the_number_it_was_given() -> None:
    model = ScriptedChatModel(
        [
            _looking("c1", "protein.md"),
            ModelReply(text="1.6 g per kg [1]."),
            _looking("c2", "protein.md"),
            ModelReply(text="Still 1.6 g per kg [1]."),
        ]
    )
    app = _app(model)

    app.agent.answer("How much protein?", THREAD)
    again = app.agent.answer("Say that again?", THREAD)

    assert [(c.number, c.document) for c in again.citations] == [(1, "protein.md")]


@pytest.mark.integration
def test_an_answer_echoing_an_earlier_number_resolves_to_that_source() -> None:
    """The citation a model repeats while paraphrasing itself now resolves against
    the conversation, so it points where the user was told it pointed."""
    model = ScriptedChatModel(
        [
            _looking("c1", "protein.md"),
            ModelReply(text="1.6 g per kg [1]."),
            ModelReply(text="As I said, 1.6 g per kg [1]."),
        ]
    )
    app = _app(model)

    app.agent.answer("How much protein?", THREAD)
    echoed = app.agent.answer("Remind me?", THREAD)

    assert [(c.number, c.document) for c in echoed.citations] == [(1, "protein.md")]


@pytest.mark.integration
def test_each_turn_gets_the_whole_round_budget() -> None:
    """A budget spent across the conversation would leave a long chat unable to run
    a single tool."""
    model = ScriptedChatModel(
        [
            _searching("c1"),
            ModelReply(text="1.6 g per kg [1]."),
            _searching("c2"),
            ModelReply(text="Still 1.6 g per kg [1]."),
        ]
    )
    app = _app(model, rounds=2)

    app.agent.answer("How much protein?", THREAD)
    second = app.agent.answer("Say that again?", THREAD)

    assert second.answer == "Still 1.6 g per kg [1]."


@pytest.mark.integration
def test_a_turn_that_spends_its_budget_does_not_spend_the_next_ones() -> None:
    class _SearchesForever:
        def __init__(self) -> None:
            self.completions = 0

        def complete(
            self,
            messages: tuple[Message, ...],
            tools: tuple[Tool, ...],
            on_text: TextSink = unheard,
        ) -> ModelReply:
            self.completions += 1
            if self.completions > 2:
                return ModelReply(text="Fine: 1.6 g per kg.")
            return _searching(f"c{self.completions}")

    app = _app(_SearchesForever(), rounds=2)

    with pytest.raises(ToolLoopLimitError):
        app.agent.answer("How much protein?", THREAD)

    assert app.agent.answer("Just tell me.", THREAD).answer == "Fine: 1.6 g per kg."


@pytest.mark.integration
def test_the_trace_a_turn_returns_is_that_turns_alone() -> None:
    model = ScriptedChatModel(
        [
            _searching("c1"),
            ModelReply(text="1.6 g per kg [1]."),
            ModelReply(text="Hello!"),
        ]
    )
    app = _app(model)

    app.agent.answer("How much protein?", THREAD)
    greeting = app.agent.answer("Hi!", THREAD)

    assert [step.summary for step in greeting.trace] == [
        "Started to screen",
        "Started to route",
        f"Focused on {DEFAULT_SCOPE} — {NO_FIELD_LOADED}",
        "Started to focus",
        "Started to work",
        "Decided no tool was needed",
        "Started to answer",
    ], "the turn before it searched, and none of that is this turn's"


@pytest.mark.integration
def test_two_conversations_on_one_app_know_nothing_of_each_other() -> None:
    model = ScriptedChatModel([ModelReply(text="ok"), ModelReply(text="ok")])
    app = _app(model)

    app.agent.answer("I am talking here.", "mine")
    app.agent.answer("And I here.", "yours")

    assert model.last_messages is not None
    assert [m.content for m in model.last_messages[1:]] == ["And I here."]


@pytest.mark.integration
def test_an_answer_belongs_to_the_turn_that_asked_for_it() -> None:
    """`answer` is a per-turn key on a thread that keeps everything. A regression test
    rather than a guard, and deliberately so: a final reply is one with no tool calls,
    so the router only reaches `done` after this turn has written its own answer. The
    reset in `ScreenStep` is belt and braces, pinned by the unit assertion on what
    that step returns."""
    model = ScriptedChatModel(
        [ModelReply(text="1.6 g per kg."), ModelReply(text="Five grams.")]
    )
    app = _app(model)

    first = app.agent.answer("How much protein?", THREAD)
    second = app.agent.answer("And creatine?", THREAD)

    assert first.answer == "1.6 g per kg."
    assert second.answer == "Five grams."
