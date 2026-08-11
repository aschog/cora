import pytest

from cora.app.assembly import App, assemble
from cora.core.errors import LlmError, ToolLoopLimitError
from cora.core.ports.chat_model import ChatModel, Message, ModelReply
from cora.core.ports.plugin import Tool, ToolCall
from cora.core.services.retrieval_tool import SEARCH_TOOL_NAME
from cora.core.trace import Reconsidered, ToolUse
from fakes import CountingRetriever, FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin

SEED_DOC = ("protein.md", b"aim for 1.6 g of protein per kg")
OFF_THE_CUFF = "Beginners should train three times a week."
GROUNDED = "Your notes say 1.6 g per kg [1]."
REMINDER = "You answered without searching. Search the documents first."
FABRICATED = "Protein is 1.6 g per kg [1]."


def _assemble_with(chat_model: ChatModel, max_tool_rounds: int = 8) -> App:
    return assemble(
        chat_model=chat_model,
        embedder=FakeEmbedder(),
        retriever=CountingRetriever(),
        plugin=make_plugin(seed_docs=(SEED_DOC,), grounding=REMINDER),
        max_tool_rounds=max_tool_rounds,
    )


def _assemble(replies: list[ModelReply], retriever: FakeRetriever) -> App:
    return assemble(
        chat_model=ScriptedChatModel(replies),
        embedder=FakeEmbedder(),
        retriever=retriever,
        plugin=make_plugin(seed_docs=(SEED_DOC,), grounding=REMINDER),
    )


def _searching() -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(
                name=SEARCH_TOOL_NAME, arguments={"query": "protein"}, call_id="c1"
            ),
        )
    )


@pytest.mark.integration
def test_an_answer_that_skipped_the_documents_is_sent_back_for_them() -> None:
    retriever = CountingRetriever()
    app = _assemble(
        [ModelReply(text=OFF_THE_CUFF), _searching(), ModelReply(text=GROUNDED)],
        retriever,
    )

    result = app.agent.answer("How much protein should I eat?")

    assert result.answer == GROUNDED
    assert [source.name for source in result.sources] == ["protein.md"]
    assert retriever.queries == 1


@pytest.mark.integration
def test_the_trace_shows_the_answer_being_sent_back() -> None:
    app = _assemble(
        [ModelReply(text=OFF_THE_CUFF), _searching(), ModelReply(text=GROUNDED)],
        CountingRetriever(),
    )

    result = app.agent.answer("How much protein should I eat?")

    kinds = [type(step) for step in result.trace]
    assert Reconsidered in kinds
    assert kinds.index(Reconsidered) < kinds.index(ToolUse)


@pytest.mark.integration
def test_small_talk_is_still_answered_without_the_documents() -> None:
    retriever = CountingRetriever()
    app = _assemble(
        [ModelReply(text="Hello!"), ModelReply(text="Hello again!")], retriever
    )

    result = app.agent.answer("Hi there!")

    assert result.answer == "Hello again!"
    assert retriever.queries == 0
    assert result.sources == ()


class _DiesAfterTheNudge:
    """Answers, then fails the round the gate asks for."""

    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.completions += 1
        if self.completions == 1:
            return ModelReply(text=OFF_THE_CUFF)
        raise LlmError


class _DiesAfterSearching:
    """Answers, searches when told to, then dies with the documents in hand."""

    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.completions += 1
        if self.completions == 1:
            return ModelReply(text=FABRICATED)
        if self.completions == 2:
            return _searching()
        raise LlmError


@pytest.mark.integration
def test_a_dead_second_look_gives_back_the_answer_it_was_second_guessing() -> None:
    app = _assemble_with(_DiesAfterTheNudge())

    result = app.agent.answer("How much protein should I eat?")

    assert result.answer == OFF_THE_CUFF
    assert result.sources == ()


@pytest.mark.integration
def test_a_failure_after_the_second_look_worked_is_not_forgiven() -> None:
    """Once the gate's round has been and gone, the run is an ordinary run: an
    answer from before the search is not an answer to the search."""
    app = _assemble_with(_DiesAfterSearching())

    with pytest.raises(LlmError):
        app.agent.answer("How much protein should I eat?")


@pytest.mark.integration
def test_the_friendly_give_up_is_never_swallowed_by_the_gate() -> None:
    app = _assemble_with(_SearchesForever(), max_tool_rounds=3)

    with pytest.raises(ToolLoopLimitError):
        app.agent.answer("How much protein should I eat?")


class _SearchesForever:
    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.completions += 1
        if self.completions == 1:
            return ModelReply(text=OFF_THE_CUFF)
        return _searching()


@pytest.mark.integration
def test_a_plugin_that_asks_for_no_grounding_answers_in_one_round() -> None:
    retriever = CountingRetriever()
    app = assemble(
        chat_model=ScriptedChatModel([ModelReply(text=OFF_THE_CUFF)]),
        embedder=FakeEmbedder(),
        retriever=retriever,
        plugin=make_plugin(seed_docs=(SEED_DOC,)),
    )

    result = app.agent.answer("How much protein should I eat?")

    assert result.answer == OFF_THE_CUFF
    assert retriever.queries == 0
