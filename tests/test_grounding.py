import pytest

from cora.app.assembly import App, assemble
from cora.core.metadata_filter import MetadataFilter
from cora.core.ports.chat_model import ModelReply
from cora.core.ports.plugin import ToolCall
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.services.retrieval_tool import SEARCH_TOOL_NAME
from cora.core.trace import Reconsidered, ToolUse
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin

SEED_DOC = ("protein.md", b"aim for 1.6 g of protein per kg")
OFF_THE_CUFF = "Beginners should train three times a week."
GROUNDED = "Your notes say 1.6 g per kg [1]."
REMINDER = "You answered without searching. Search the documents first."


class _CountingRetriever(FakeRetriever):
    def __init__(self) -> None:
        super().__init__()
        self.queries = 0

    def query(
        self,
        query_vector: list[float],
        k: int,
        metadata_filter: MetadataFilter | None = None,
    ) -> list[RetrievedChunk]:
        self.queries += 1
        return super().query(query_vector, k, metadata_filter)


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
    retriever = _CountingRetriever()
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
        _CountingRetriever(),
    )

    result = app.agent.answer("How much protein should I eat?")

    kinds = [type(step) for step in result.trace]
    assert Reconsidered in kinds
    assert kinds.index(Reconsidered) < kinds.index(ToolUse)


@pytest.mark.integration
def test_small_talk_is_still_answered_without_the_documents() -> None:
    retriever = _CountingRetriever()
    app = _assemble(
        [ModelReply(text="Hello!"), ModelReply(text="Hello again!")], retriever
    )

    result = app.agent.answer("Hi there!")

    assert result.answer == "Hello again!"
    assert retriever.queries == 0
    assert result.sources == ()


@pytest.mark.integration
def test_a_plugin_that_asks_for_no_grounding_answers_in_one_round() -> None:
    retriever = _CountingRetriever()
    app = assemble(
        chat_model=ScriptedChatModel([ModelReply(text=OFF_THE_CUFF)]),
        embedder=FakeEmbedder(),
        retriever=retriever,
        plugin=make_plugin(seed_docs=(SEED_DOC,)),
    )

    result = app.agent.answer("How much protein should I eat?")

    assert result.answer == OFF_THE_CUFF
    assert retriever.queries == 0
