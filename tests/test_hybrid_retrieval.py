from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

from cora.adapters.bm25_keyword_index import Bm25KeywordIndex
from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder
from cora.app.assembly import assemble
from cora.engine.hybrid_context_source import HybridContextSource
from cora.ports.chat_model import ModelReply
from fakes import ScriptedChatModel
from fixture_plugins import make_plugin

if TYPE_CHECKING:
    from cora.adapters.chroma_retriever import ChromaRetriever

pytestmark = pytest.mark.integration

_DOCS = (
    (
        "paraphrase.md",
        b"Muscular development and raw strength arise from progressive overload, "
        b"sufficient rest, and steady effort sustained across many months of work.",
    ),
    (
        "literal.md",
        b"The locker rooms open at six each morning and members must bring their "
        b"own padlock and towel. Water fountains sit by the entrance. Bigger "
        b"stronger muscles reward those who show up and train with intent daily.",
    ),
    (
        "sleep.md",
        b"Sleep drives recovery. Aim for eight hours nightly so the body repairs "
        b"tissue and consolidates adaptations after demanding training sessions.",
    ),
    (
        "warmup.md",
        b"A thorough warm up raises core temperature and primes the nervous system "
        b"with dynamic drills and light ramp-up sets before the working weight.",
    ),
)


def test_hybrid_surfaces_a_lexical_match_dense_ranks_below_top_k(
    make_chroma: "Callable[[], ChromaRetriever]",
) -> None:
    app = assemble(
        chat_model=ScriptedChatModel([ModelReply(text="ok")]),
        embedder=SentenceTransformerEmbedder(),
        retriever=make_chroma(),
        plugin=make_plugin(seed_docs=_DOCS),
        retrieval="hybrid",
        keyword_index=Bm25KeywordIndex(),
    )
    question = "how to get bigger stronger muscles"

    dense = [hit.chunk.source for hit in app.knowledge_base.search(question, k=2)]
    source = app.context_source
    assert isinstance(source, HybridContextSource)
    hybrid = [hit.chunk.source for hit in source.search(question, k=2)]

    assert "literal.md" not in dense
    assert "literal.md" in hybrid
