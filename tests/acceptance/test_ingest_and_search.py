from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

from app_builder import assembled, indexed
from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import TEXT_LOADERS, ScriptedChatModel

if TYPE_CHECKING:
    from cora.adapters.chroma_retriever import ChromaRetriever

pytestmark = pytest.mark.integration

FACTS = (
    ("The Eiffel Tower is a wrought-iron lattice tower in Paris, France. " * 20)
    + "\n\n"
    + ("Python is a high-level general-purpose programming language. " * 20)
    + "\n\n"
    + ("Photosynthesis lets plants convert sunlight into chemical energy. " * 20)
).encode()


def test_a_search_retrieves_the_chunk_matching_the_question(
    make_chroma: "Callable[[], ChromaRetriever]",
) -> None:
    kb = KnowledgeBase(
        embedder=SentenceTransformerEmbedder(),
        retriever=make_chroma(),
        loaders=TEXT_LOADERS,
    )
    added = kb.add_file(FACTS, "facts.txt")
    assert added >= 3

    hits = kb.search("Where is the Eiffel Tower located?", k=1)

    assert hits
    assert "Eiffel Tower" in hits[0].chunk.text
    assert hits[0].chunk.source == "facts.txt"


def test_the_agent_answers_from_the_uploaded_document_and_cites_it(
    make_chroma: "Callable[[], ChromaRetriever]",
) -> None:
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
            retriever=make_chroma(),
        ),
        ("facts.txt", FACTS),
    )

    result = app.agent.answer("Where is the Eiffel Tower?", "t1")

    assert result.answer == "It stands in Paris [1]."
    assert [(source.number, source.name) for source in result.sources] == [
        (1, "facts.txt")
    ]
