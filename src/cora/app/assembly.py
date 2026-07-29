from dataclasses import dataclass
from typing import Protocol

from cora.adapters.port_logging import (
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
)
from cora.app.config import (
    DEFAULT_FUSION_QUERIES,
    DEFAULT_HISTORY_TURNS,
    DEFAULT_MAX_TOOL_ROUNDS,
    DEFAULT_RETRIEVAL,
    DEFAULT_TOP_K,
    RETRIEVAL_ADVANCED,
    RETRIEVAL_HYBRID,
    Config,
)
from cora.app.log_config import enable_debug_logs
from cora.core.chunk import Chunk
from cora.core.errors import ConfigurationError
from cora.core.ports.chat_model import ChatModel
from cora.core.ports.embedding import Embedder
from cora.core.ports.plugin import Plugin
from cora.core.ports.retrieval import RetrievedChunk, Retriever
from cora.core.services.chat_engine import ChatEngine, ContextSource
from cora.core.services.fusion_context_source import FusionContextSource
from cora.core.services.hybrid_context_source import HybridContextSource
from cora.core.services.knowledge_base import KnowledgeBase
from cora.core.services.plugin_registry import load_plugin
from cora.core.services.query_planner import QueryPlanner
from cora.core.services.tool_runtime import ToolRuntime
from cora.core.services.validation import (
    EmptyInputRule,
    MaxLengthRule,
    ValidationPipeline,
)

MAX_INPUT_CHARS = 4000
DEFAULT_COLLECTION = "documents"


class KeywordStore(Protocol):
    def add(self, chunks: list[Chunk]) -> None: ...

    def search(self, query: str, k: int) -> list[RetrievedChunk]: ...


@dataclass(frozen=True)
class App:
    engine: ChatEngine
    knowledge_base: KnowledgeBase


def assemble(
    *,
    chat_model: ChatModel,
    embedder: Embedder,
    retriever: Retriever,
    plugin: Plugin,
    top_k: int = DEFAULT_TOP_K,
    max_tool_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
    history_turns: int = DEFAULT_HISTORY_TURNS,
    retrieval: str = DEFAULT_RETRIEVAL,
    fusion_queries: int = DEFAULT_FUSION_QUERIES,
    keyword_index: KeywordStore | None = None,
    debug: bool = False,
) -> App:
    if debug:
        chat_model = LoggingChatModel(chat_model)
        embedder = LoggingEmbedder(embedder)
        retriever = LoggingRetriever(retriever)
    knowledge_base = KnowledgeBase(
        embedder=embedder, retriever=retriever, keyword_index=keyword_index
    )
    for filename, data in plugin.seed_docs:
        knowledge_base.add_file(data, filename)
    context_source = _context_source(
        retrieval, chat_model, knowledge_base, fusion_queries, keyword_index
    )
    validation = ValidationPipeline(
        core_rules=(EmptyInputRule(), MaxLengthRule(MAX_INPUT_CHARS)),
        plugin_rules=plugin.validation_rules,
    )
    engine = ChatEngine(
        chat_model=chat_model,
        knowledge_base=context_source,
        validation=validation,
        tool_runtime=ToolRuntime(tools=plugin.tools),
        top_k=top_k,
        max_tool_rounds=max_tool_rounds,
        max_history_turns=history_turns,
        system_prompt=plugin.system_prompt,
        tools=plugin.tools,
    )
    return App(engine=engine, knowledge_base=knowledge_base)


def _context_source(
    retrieval: str,
    chat_model: ChatModel,
    knowledge_base: KnowledgeBase,
    fusion_queries: int,
    keyword_index: KeywordStore | None,
) -> ContextSource:
    if retrieval == RETRIEVAL_ADVANCED:
        planner = QueryPlanner(chat_model=chat_model, num_queries=fusion_queries)
        return FusionContextSource(planner=planner, index=knowledge_base)
    if retrieval == RETRIEVAL_HYBRID:
        if keyword_index is None:
            raise ConfigurationError("Hybrid retrieval requires a keyword index.")
        return HybridContextSource(dense=knowledge_base, keyword=keyword_index)
    return knowledge_base


def build(config: Config, collection: str = DEFAULT_COLLECTION) -> App:
    from cora.adapters.bm25_keyword_index import Bm25KeywordIndex
    from cora.adapters.chroma_retriever import ChromaRetriever
    from cora.adapters.openrouter_chat_model import OpenRouterChatModel
    from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder

    enable_debug_logs(config.debug)
    retriever = ChromaRetriever(path=config.db_path, collection=collection)
    keyword_index = (
        Bm25KeywordIndex.from_chunks(retriever.all_chunks())
        if config.retrieval == RETRIEVAL_HYBRID
        else None
    )
    return assemble(
        chat_model=OpenRouterChatModel(
            model=config.model, api_key=config.api_key, base_url=config.base_url
        ),
        embedder=SentenceTransformerEmbedder(),
        retriever=retriever,
        plugin=load_plugin(config.plugin_module),
        top_k=config.top_k,
        max_tool_rounds=config.max_tool_rounds,
        history_turns=config.history_turns,
        retrieval=config.retrieval,
        fusion_queries=config.fusion_queries,
        keyword_index=keyword_index,
        debug=config.debug,
    )
