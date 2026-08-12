from collections.abc import Callable
from typing import Protocol

from cora.domain.errors import ConfigurationError
from cora.engine.fusion_context_source import FusionContextSource
from cora.engine.hybrid_context_source import HybridContextSource
from cora.engine.knowledge_base import KeywordIndex, KnowledgeBase
from cora.engine.query_planner import QueryPlanner
from cora.ports.chat_model import ChatModel
from cora.ports.context_source import ContextSource

RETRIEVAL_PLAIN = "plain"
RETRIEVAL_ADVANCED = "advanced"
RETRIEVAL_HYBRID = "hybrid"
DEFAULT_RETRIEVAL = RETRIEVAL_PLAIN


class KeywordStore(KeywordIndex, ContextSource, Protocol):
    """The injected sparse index: written to on ingest, searched during hybrid."""


RetrievalBuilder = Callable[
    [ChatModel, KnowledgeBase, KeywordStore | None, int], ContextSource
]


def _plain(
    chat_model: ChatModel,
    knowledge_base: KnowledgeBase,
    keyword_index: KeywordStore | None,
    fusion_queries: int,
) -> ContextSource:
    return knowledge_base


def _advanced(
    chat_model: ChatModel,
    knowledge_base: KnowledgeBase,
    keyword_index: KeywordStore | None,
    fusion_queries: int,
) -> ContextSource:
    planner = QueryPlanner(chat_model=chat_model, num_queries=fusion_queries)
    return FusionContextSource(planner=planner, index=knowledge_base)


def _hybrid(
    chat_model: ChatModel,
    knowledge_base: KnowledgeBase,
    keyword_index: KeywordStore | None,
    fusion_queries: int,
) -> ContextSource:
    if keyword_index is None:
        raise ConfigurationError("Hybrid retrieval requires a keyword index.")
    return HybridContextSource(dense=knowledge_base, keyword=keyword_index)


RETRIEVAL_BUILDERS: dict[str, RetrievalBuilder] = {
    RETRIEVAL_PLAIN: _plain,
    RETRIEVAL_ADVANCED: _advanced,
    RETRIEVAL_HYBRID: _hybrid,
}
RETRIEVAL_MODES = tuple(RETRIEVAL_BUILDERS)
NEEDS_KEYWORD_INDEX = frozenset({RETRIEVAL_HYBRID})


def needs_keyword_index(mode: str) -> bool:
    return mode in NEEDS_KEYWORD_INDEX


def build_context_source(
    mode: str,
    *,
    chat_model: ChatModel,
    knowledge_base: KnowledgeBase,
    keyword_index: KeywordStore | None,
    fusion_queries: int,
) -> ContextSource:
    return RETRIEVAL_BUILDERS[mode](
        chat_model, knowledge_base, keyword_index, fusion_queries
    )
