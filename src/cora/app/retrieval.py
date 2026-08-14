from collections.abc import Callable

from cora.engine.fusion_context_source import FusionContextSource
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.query_planner import QueryPlanner
from cora.ports.chat_model import ChatModel
from cora.ports.context_source import ContextSource

RETRIEVAL_PLAIN = "plain"
RETRIEVAL_ADVANCED = "advanced"
DEFAULT_RETRIEVAL = RETRIEVAL_PLAIN

RetrievalBuilder = Callable[[ChatModel, KnowledgeBase, int], ContextSource]


def _plain(
    chat_model: ChatModel, knowledge_base: KnowledgeBase, fusion_queries: int
) -> ContextSource:
    return knowledge_base


def _advanced(
    chat_model: ChatModel, knowledge_base: KnowledgeBase, fusion_queries: int
) -> ContextSource:
    planner = QueryPlanner(chat_model=chat_model, num_queries=fusion_queries)
    return FusionContextSource(planner=planner, index=knowledge_base)


RETRIEVAL_BUILDERS: dict[str, RetrievalBuilder] = {
    RETRIEVAL_PLAIN: _plain,
    RETRIEVAL_ADVANCED: _advanced,
}
RETRIEVAL_MODES = tuple(RETRIEVAL_BUILDERS)


def build_context_source(
    mode: str,
    *,
    chat_model: ChatModel,
    knowledge_base: KnowledgeBase,
    fusion_queries: int,
) -> ContextSource:
    return RETRIEVAL_BUILDERS[mode](chat_model, knowledge_base, fusion_queries)
