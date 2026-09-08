from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from app_builder import assembled, indexed
from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder
from cora.domain.trace import ToolUse
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.engine.scoping import running_in
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import TEXT_LOADERS, FakeDocuments, ScriptedChatModel

if TYPE_CHECKING:
    from cora.adapters.sqlite_vec_retriever import SqliteVecRetriever

pytestmark = pytest.mark.integration

FACTS = (
    ("The Eiffel Tower is a wrought-iron lattice tower in Paris, France. " * 20)
    + "\n\n"
    + ("Python is a high-level general-purpose programming language. " * 20)
    + "\n\n"
    + ("Photosynthesis lets plants convert sunlight into chemical energy. " * 20)
).encode()


def test_a_search_retrieves_the_chunk_matching_the_question(
    make_index: "Callable[[], SqliteVecRetriever]",
) -> None:
    kb = KnowledgeBase(
        embedder=SentenceTransformerEmbedder(),
        retriever=make_index(),
        loaders=TEXT_LOADERS,
        documents=FakeDocuments(),
    )
    added = kb.add_file(FACTS, "facts.txt")
    assert added >= 3

    hits = kb.search("Where is the Eiffel Tower located?", k=1)

    assert hits
    assert "Eiffel Tower" in hits[0].chunk.text
    assert hits[0].chunk.source == "facts.txt"


def test_the_agent_answers_from_the_uploaded_document_and_cites_it(
    make_index: "Callable[[], SqliteVecRetriever]",
) -> None:
    """`top_k=1` is what makes the retrieval decision observable: the fixture is one
    document of six chunks, so at the shipped default of five the passage the answer
    cites comes back whatever was searched for, and the assertion below holds even when
    the query never reaches the index."""
    app = indexed(
        assembled(
            chat_model=ScriptedChatModel(
                [
                    ModelReply(
                        tool_calls=(
                            ToolCall(
                                name=SEARCH_TOOL_NAME,
                                arguments={"query": "Where is the Eiffel Tower?"},
                                call_id="call-1",
                            ),
                        )
                    ),
                    ModelReply(text="It stands in Paris [1]."),
                ]
            ),
            embedder=SentenceTransformerEmbedder(),
            retriever=make_index(),
            top_k=1,
        ),
        ("facts.txt", FACTS),
    )

    result = app.agent.answer("Where is the Eiffel Tower?", "t1")

    assert result.answer == "It stands in Paris [1]."
    [lookup] = [step for step in result.trace if isinstance(step, ToolUse)]
    assert "Eiffel Tower" in lookup.detail
    assert [(c.number, c.document) for c in result.citations] == [(1, "facts.txt")]


def test_the_index_is_one_file_and_a_field_reads_only_its_own(tmp_path: Path) -> None:
    """What the change is for, stated once: two fields indexed and searched over an
    index that is a single file the deployment named."""
    from cora.adapters.sqlite_vec_retriever import SqliteVecRetriever

    index = tmp_path / "cora.sqlite"
    kb = KnowledgeBase(
        embedder=SentenceTransformerEmbedder(),
        retriever=SqliteVecRetriever.at(str(index)),
        loaders=TEXT_LOADERS,
        documents=FakeDocuments(),
    )
    kb.add_file(FACTS, "facts.txt", scope="travel")
    kb.add_file(b"Deadlifts train the posterior chain. " * 40, "lifts.txt", "fitness")

    with running_in(frozenset({"travel"})):
        hits = kb.search("Where is the Eiffel Tower located?", k=1)

    assert index.is_file()
    assert [hit.chunk.source for hit in hits] == ["facts.txt"]
    assert kb.list_sources("fitness") == ["lifts.txt"]
