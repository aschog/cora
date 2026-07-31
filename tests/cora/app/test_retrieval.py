import pytest

from cora.app.retrieval import (
    RETRIEVAL_BUILDERS,
    RETRIEVAL_MODES,
    build_context_source,
)
from cora.core.errors import ConfigurationError
from cora.core.ports.chat_model import ModelReply
from cora.core.services.knowledge_base import KnowledgeBase
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel


def _kb() -> KnowledgeBase:
    return KnowledgeBase(embedder=FakeEmbedder(), retriever=FakeRetriever())


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


def test_hybrid_without_a_keyword_index_is_rejected() -> None:
    with pytest.raises(ConfigurationError):
        build_context_source(
            "hybrid",
            chat_model=_chat(),
            knowledge_base=_kb(),
            keyword_index=None,
            fusion_queries=4,
        )
