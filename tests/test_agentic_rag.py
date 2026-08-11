from cora.app.assembly import App, assemble
from cora.core.metadata_filter import MetadataFilter
from cora.core.ports.chat_model import ModelReply
from cora.core.ports.plugin import ToolCall
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.trace import ToolUse
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel, add_tool
from fixture_plugins import make_plugin

SEED_DOC = ("note.md", b"protein builds muscle")
QUESTION = "What do my notes say about protein, and what is 20 + 22?"
ANSWER = "Protein builds muscle [1], and 20 + 22 = 42."


class CountingRetriever(FakeRetriever):
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


def _call(name: str, call_id: str, **arguments: object) -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name=name, arguments=arguments, call_id=call_id),)
    )


def _assemble(replies: list[ModelReply], retriever: FakeRetriever) -> App:
    return assemble(
        chat_model=ScriptedChatModel(replies),
        embedder=FakeEmbedder(),
        retriever=retriever,
        plugin=make_plugin(tools=(add_tool(),), seed_docs=(SEED_DOC,)),
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

    result = app.agent.answer(QUESTION)

    assert result.answer == ANSWER
    assert [(source.number, source.name) for source in result.sources] == [
        (1, "note.md")
    ]
    lookup, calculation = [step for step in result.trace if isinstance(step, ToolUse)]
    assert "protein builds muscle" in lookup.detail
    assert calculation.outcome == "42"


def test_a_question_needing_neither_retrieves_nothing_and_calls_no_tool() -> None:
    retriever = CountingRetriever()
    app = _assemble([ModelReply(text="Hello! How can I help?")], retriever)

    result = app.agent.answer("Hello there!")

    assert result.answer == "Hello! How can I help?"
    assert [step for step in result.trace if isinstance(step, ToolUse)] == []
    assert result.sources == ()
    assert retriever.queries == 0
