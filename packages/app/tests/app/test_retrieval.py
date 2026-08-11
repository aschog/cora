import pytest

from cora.app.retrieval import (
    RETRIEVAL_BUILDERS,
    RETRIEVAL_MODES,
    build_context_source,
)
from cora.core.domain.errors import ConfigurationError
from cora.core.ports.chat_model import ModelReply
from cora.core.service_layer.fusion_context_source import FusionContextSource
from cora.core.service_layer.knowledge_base import KnowledgeBase
from fakes import TEXT_LOADERS, FakeEmbedder, FakeRetriever, ScriptedChatModel


def _kb() -> KnowledgeBase:
    return KnowledgeBase(
        embedder=FakeEmbedder(), retriever=FakeRetriever(), loaders=TEXT_LOADERS
    )


def _chat() -> ScriptedChatModel:
    return ScriptedChatModel([ModelReply(text="ok")])


def test_allowed_modes_are_exactly_the_registered_builders() -> None:
    assert tuple(RETRIEVAL_BUILDERS) == RETRIEVAL_MODES


def test_plain_mode_returns_the_knowledge_base_itself() -> None:
    kb = _kb()

    source = build_context_source(
        "plain",
        chat_model=_chat(),
        knowledge_base=kb,
        keyword_index=None,
        fusion_queries=4,
    )

    assert source is kb


def test_advanced_mode_wraps_the_knowledge_base_in_fusion() -> None:
    source = build_context_source(
        "advanced",
        chat_model=_chat(),
        knowledge_base=_kb(),
        keyword_index=None,
        fusion_queries=3,
    )

    assert isinstance(source, FusionContextSource)


def test_hybrid_without_a_keyword_index_is_rejected() -> None:
    with pytest.raises(ConfigurationError):
        build_context_source(
            "hybrid",
            chat_model=_chat(),
            knowledge_base=_kb(),
            keyword_index=None,
            fusion_queries=4,
        )
