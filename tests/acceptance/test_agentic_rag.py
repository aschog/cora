import pytest

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.domain.trace import ModelDecision, ScopeSettled, StepEntered, ToolUse
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import CountingRetriever, FakeRetriever, ScriptedChatModel, add_tool
from fixture_plugins import make_plugin

SEED_DOC = ("note.md", b"protein builds muscle")
THREAD = "t1"
QUESTION = "What do my notes say about protein, and what is 20 + 22?"
ANSWER = "Protein builds muscle [1], and 20 + 22 = 42."
OFF_THE_CUFF = "Three times a week is plenty for a beginner."
CITED = "Your notes say protein builds muscle [1]."
SENT_BACK = "Your notes say 1.6 g of protein per kg [1]."


def _call(name: str, call_id: str, **arguments: object) -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name=name, arguments=arguments, call_id=call_id),)
    )


def _assemble(replies: list[ModelReply], retriever: FakeRetriever) -> App:
    return indexed(
        assembled(
            chat_model=ScriptedChatModel(replies),
            retriever=retriever,
            plugin=make_plugin(tools=(add_tool(),)),
        ),
        SEED_DOC,
    )


def test_a_question_needing_a_lookup_and_a_calculation_uses_both() -> None:
    app = _assemble(
        [
            _call("search_documents", "call-1", query="protein"),
            _call("add", "call-2", a=20, b=22),
            ModelReply(text=ANSWER),
        ],
        CountingRetriever(),
    )

    result = app.agent.answer(QUESTION, THREAD)

    assert result.answer == ANSWER
    assert [(c.number, c.document) for c in result.citations] == [(1, "note.md")]
    lookup, calculation = [step for step in result.trace if isinstance(step, ToolUse)]
    assert "protein builds muscle" in lookup.detail
    assert calculation.outcome == "42"


def test_a_question_needing_neither_retrieves_nothing_and_calls_no_tool() -> None:
    retriever = CountingRetriever()
    app = _assemble([ModelReply(text="Hello! How can I help?")], retriever)

    result = app.agent.answer("Hello there!", THREAD)

    assert result.answer == "Hello! How can I help?"
    assert [step for step in result.trace if isinstance(step, ToolUse)] == []
    assert result.citations == ()
    assert retriever.queries == 0


def test_an_answer_the_model_gave_without_searching_stands() -> None:
    """The turn is one path: nothing searches on the model's behalf, so an answer that
    skipped the documents is the answer the user reads."""
    retriever = CountingRetriever()
    app = indexed(
        assembled(
            chat_model=ScriptedChatModel(
                [ModelReply(text=OFF_THE_CUFF), ModelReply(text=SENT_BACK)]
            ),
            retriever=retriever,
        ),
        SEED_DOC,
    )

    result = app.agent.answer("How often should a beginner train?", THREAD)

    assert result.answer == OFF_THE_CUFF
    assert retriever.queries == 0
    assert [
        type(step) for step in result.trace if not isinstance(step, StepEntered)
    ] == [ScopeSettled, ModelDecision], "one round, and nothing searched in it"


@pytest.mark.integration
def test_a_document_question_is_answered_the_round_after_the_search_returns() -> None:
    """Two model calls and one search: the round that asks, and the round that reads
    what came back."""
    model = ScriptedChatModel(
        [_call("search_documents", "call-1", query="protein"), ModelReply(text=CITED)]
    )
    retriever = CountingRetriever()
    app = indexed(assembled(chat_model=model, retriever=retriever), SEED_DOC)

    result = app.agent.answer("What do my notes say about protein?", THREAD)

    assert result.answer == CITED
    assert model.completions == 2
    assert retriever.queries == 1
    assert [c.document for c in result.citations] == ["note.md"]
