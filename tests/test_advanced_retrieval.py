from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

from cora.engine.fusion_context_source import FusionContextSource
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.query_planner import QueryPlanner
from cora.ports.chat_model import ModelReply
from fakes import TEXT_LOADERS, FakeEmbedder, ScriptedChatModel

if TYPE_CHECKING:
    from cora.adapters.chroma_retriever import ChromaRetriever

pytestmark = pytest.mark.integration


def test_advanced_retrieval_filters_by_source_and_fuses(
    make_chroma: "Callable[[], ChromaRetriever]",
) -> None:
    kb = KnowledgeBase(
        embedder=FakeEmbedder(), retriever=make_chroma(), loaders=TEXT_LOADERS
    )
    kb.add_file(("protein supports muscle growth " * 40).encode(), "protein.md")
    kb.add_file(("energy balance drives weight change " * 40).encode(), "energy.md")

    plan = '{"queries": ["protein intake", "protein timing"], "source": "protein.md"}'
    planner = QueryPlanner(
        chat_model=ScriptedChatModel([ModelReply(text=plan)]), num_queries=2
    )
    fusion = FusionContextSource(planner=planner, index=kb)

    hits = fusion.search("how much protein should I eat?", k=5)

    assert hits
    assert {hit.chunk.source for hit in hits} == {"protein.md"}
