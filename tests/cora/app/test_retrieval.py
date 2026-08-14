import pytest

from cora.app.retrieval import (
    RETRIEVAL_ADVANCED,
    RETRIEVAL_BUILDERS,
    RETRIEVAL_MODES,
    RETRIEVAL_PLAIN,
    build_context_source,
)
from cora.engine.fusion_context_source import FusionContextSource
from cora.engine.knowledge_base import KnowledgeBase
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel


def test_allowed_modes_are_exactly_the_registered_builders() -> None:
    assert tuple(RETRIEVAL_BUILDERS) == RETRIEVAL_MODES


def test_plain_searches_the_index_the_documents_were_written_to() -> None:
    knowledge_base = _knowledge_base()

    assert _built(RETRIEVAL_PLAIN, knowledge_base) is knowledge_base


def test_advanced_plans_queries_and_fuses_what_the_same_index_returns() -> None:
    knowledge_base = _knowledge_base()

    source = _built(RETRIEVAL_ADVANCED, knowledge_base)

    assert isinstance(source, FusionContextSource)
    assert source.index is knowledge_base


def test_a_mode_no_builder_answers_to_is_refused_by_name() -> None:
    with pytest.raises(KeyError):
        _built("hybrid", _knowledge_base())


def _knowledge_base() -> KnowledgeBase:
    return KnowledgeBase(embedder=FakeEmbedder(), retriever=FakeRetriever(), loaders={})


def _built(mode: str, knowledge_base: KnowledgeBase) -> object:
    return build_context_source(
        mode,
        chat_model=ScriptedChatModel([]),
        knowledge_base=knowledge_base,
        fusion_queries=3,
    )
