from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder
from cora.engine.knowledge_base import KnowledgeBase
from fakes import TEXT_LOADERS

if TYPE_CHECKING:
    from cora.adapters.chroma_retriever import ChromaRetriever

pytestmark = pytest.mark.integration


def test_a_search_retrieves_the_chunk_matching_the_question(
    make_chroma: "Callable[[], ChromaRetriever]",
) -> None:
    kb = KnowledgeBase(
        embedder=SentenceTransformerEmbedder(),
        retriever=make_chroma(),
        loaders=TEXT_LOADERS,
    )
    eiffel = "The Eiffel Tower is a wrought-iron lattice tower in Paris, France. " * 20
    coding = "Python is a high-level general-purpose programming language. " * 20
    plants = "Photosynthesis lets plants convert sunlight into chemical energy. " * 20
    data = f"{eiffel}\n\n{coding}\n\n{plants}".encode()

    added = kb.add_file(data, "facts.txt")
    assert added >= 3

    hits = kb.search("Where is the Eiffel Tower located?", k=1)

    assert hits
    assert "Eiffel Tower" in hits[0].chunk.text
    assert hits[0].chunk.source == "facts.txt"
