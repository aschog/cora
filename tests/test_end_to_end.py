from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

from core.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder
from core.services.knowledge_base import KnowledgeBase

if TYPE_CHECKING:
    from core.adapters.chroma_retriever import ChromaRetriever

pytestmark = pytest.mark.integration


def test_ingest_and_search_end_to_end(
    make_chroma: "Callable[[], ChromaRetriever]",
) -> None:
    kb = KnowledgeBase(
        embedder=SentenceTransformerEmbedder(),
        retriever=make_chroma(),
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
