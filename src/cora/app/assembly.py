from dataclasses import dataclass

from cora.adapters.langgraph_runner import LangGraphRunner, recursion_limit_for
from cora.adapters.port_logging import (
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
)
from cora.app.config import (
    DEFAULT_FUSION_QUERIES,
    DEFAULT_HISTORY_TURNS,
    DEFAULT_MAX_TOOL_ROUNDS,
    DEFAULT_TOP_K,
    Config,
)
from cora.app.log_config import enable_debug_logs
from cora.app.retrieval import (
    DEFAULT_RETRIEVAL,
    KeywordStore,
    build_context_source,
    needs_keyword_index,
)
from cora.core.context_source import ContextSource
from cora.core.errors import ConfigurationError
from cora.core.ports.chat_model import ChatModel
from cora.core.ports.embedding import Embedder
from cora.core.ports.plugin import Plugin, Tool
from cora.core.ports.retrieval import Retriever
from cora.core.services.agent import Agent
from cora.core.services.knowledge_base import KnowledgeBase
from cora.core.services.plugin_registry import load_plugin
from cora.core.services.retrieval_tool import SEARCH_TOOL_NAME, search_tool
from cora.core.services.steps import (
    GroundStep,
    ModelStep,
    PrepareStep,
    Router,
    ToolStep,
)
from cora.core.services.tool_runtime import ToolRuntime
from cora.core.services.validation import (
    EmptyInputRule,
    MaxLengthRule,
    PromptInjectionRule,
    ValidationPipeline,
)

MAX_INPUT_CHARS = 4000
DEFAULT_COLLECTION = "documents"


@dataclass(frozen=True)
class App:
    agent: Agent
    knowledge_base: KnowledgeBase
    context_source: ContextSource


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
    seed: bool = True,
    debug: bool = False,
) -> App:
    if debug:
        chat_model = LoggingChatModel(chat_model)
        embedder = LoggingEmbedder(embedder)
        retriever = LoggingRetriever(retriever)
    knowledge_base = KnowledgeBase(
        embedder=embedder, retriever=retriever, keyword_index=keyword_index
    )
    if seed:
        for filename, data in plugin.seed_docs:
            knowledge_base.add_file(data, filename)
    context_source = build_context_source(
        retrieval,
        chat_model=chat_model,
        knowledge_base=knowledge_base,
        keyword_index=keyword_index,
        fusion_queries=fusion_queries,
    )
    tools = _offered_tools(plugin, context_source, top_k)
    validation = ValidationPipeline(
        core_rules=(
            EmptyInputRule(),
            MaxLengthRule(MAX_INPUT_CHARS),
            PromptInjectionRule(),
        ),
        plugin_rules=plugin.validation_rules,
    )
    runner = LangGraphRunner(
        prepare=PrepareStep(
            validation=validation,
            system_prompt=plugin.system_prompt,
            max_history_turns=history_turns,
        ),
        model=ModelStep(chat_model=chat_model, tools=tools),
        tools=ToolStep(tool_runtime=ToolRuntime(tools=tools)),
        ground=GroundStep(reminder=plugin.grounding),
        router=Router(max_tool_rounds=max_tool_rounds, grounded=bool(plugin.grounding)),
        recursion_limit=recursion_limit_for(max_tool_rounds),
    )
    return App(
        agent=Agent(runner=runner),
        knowledge_base=knowledge_base,
        context_source=context_source,
    )


def _offered_tools(
    plugin: Plugin, context_source: ContextSource, top_k: int
) -> tuple[Tool, ...]:
    if any(tool.name == SEARCH_TOOL_NAME for tool in plugin.tools):
        raise ConfigurationError(
            f"A plugin tool may not be named '{SEARCH_TOOL_NAME}': "
            "that name belongs to document search."
        )
    return (search_tool(context_source, top_k), *plugin.tools)


def build(config: Config, collection: str = DEFAULT_COLLECTION) -> App:
    from cora.adapters.bm25_keyword_index import Bm25KeywordIndex
    from cora.adapters.chroma_retriever import ChromaRetriever
    from cora.adapters.openrouter_chat_model import OpenRouterChatModel
    from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder

    enable_debug_logs(config.debug)
    retriever = ChromaRetriever(path=config.db_path, collection=collection)
    keyword_index = (
        Bm25KeywordIndex.from_chunks(retriever.all_chunks())
        if needs_keyword_index(config.retrieval)
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
        seed=False,
        debug=config.debug,
    )
