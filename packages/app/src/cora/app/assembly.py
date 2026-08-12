from dataclasses import dataclass

from cora.adapters.langgraph_runner import langgraph_for
from cora.adapters.loaders import LOADERS
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
from cora.domain.errors import ConfigurationError
from cora.engine.agent import Agent
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.memory_tool import MAX_FACT_CHARS, REMEMBER_TOOL_NAME, remember_tool
from cora.engine.plugin_registry import load_plugin
from cora.engine.port_logging import (
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
)
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME, search_tool
from cora.engine.steps import (
    GroundStep,
    ModelStep,
    PrepareStep,
    Router,
    ToolStep,
)
from cora.engine.tool_runtime import ToolRuntime
from cora.engine.validation import (
    EmptyInputRule,
    MaxLengthRule,
    PromptInjectionRule,
    ValidationPipeline,
)
from cora.ports.chat_model import ChatModel
from cora.ports.context_source import ContextSource
from cora.ports.embedding import Embedder
from cora.ports.graph import GraphFor
from cora.ports.memory import Memory
from cora.ports.plugin import Plugin, Tool
from cora.ports.retrieval import Retriever

MAX_INPUT_CHARS = 4000
DEFAULT_COLLECTION = "documents"


@dataclass(frozen=True)
class App:
    agent: Agent
    knowledge_base: KnowledgeBase
    context_source: ContextSource
    memory: Memory | None = None


def assemble(
    *,
    chat_model: ChatModel,
    embedder: Embedder,
    retriever: Retriever,
    plugin: Plugin,
    memory: Memory | None = None,
    top_k: int = DEFAULT_TOP_K,
    max_tool_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
    history_turns: int = DEFAULT_HISTORY_TURNS,
    retrieval: str = DEFAULT_RETRIEVAL,
    fusion_queries: int = DEFAULT_FUSION_QUERIES,
    keyword_index: KeywordStore | None = None,
    graph: GraphFor = langgraph_for,
    debug: bool = False,
) -> App:
    if debug:
        chat_model = LoggingChatModel(chat_model)
        embedder = LoggingEmbedder(embedder)
        retriever = LoggingRetriever(retriever)
    knowledge_base = KnowledgeBase(
        embedder=embedder,
        retriever=retriever,
        loaders=LOADERS,
        keyword_index=keyword_index,
    )
    context_source = build_context_source(
        retrieval,
        chat_model=chat_model,
        knowledge_base=knowledge_base,
        keyword_index=keyword_index,
        fusion_queries=fusion_queries,
    )
    grounding = plugin.grounding.strip()
    validation = ValidationPipeline(
        core_rules=(
            EmptyInputRule(),
            MaxLengthRule(MAX_INPUT_CHARS),
            PromptInjectionRule(),
        ),
        plugin_rules=plugin.validation_rules,
    )
    tools = _offered_tools(plugin, context_source, top_k, memory)
    runner = graph(
        prepare=PrepareStep(
            validation=validation,
            system_prompt=plugin.system_prompt,
            memory=memory,
        ),
        model=ModelStep(
            chat_model=chat_model, tools=tools, max_history_turns=history_turns
        ),
        tools=ToolStep(tool_runtime=ToolRuntime(tools=tools)),
        ground=GroundStep(
            reminder=grounding, context_source=context_source, top_k=top_k
        ),
        router=Router(max_tool_rounds=max_tool_rounds, grounded=bool(grounding)),
        max_tool_rounds=max_tool_rounds,
    )
    return App(
        agent=Agent(runner=runner),
        knowledge_base=knowledge_base,
        context_source=context_source,
        memory=memory,
    )


RESERVED_TOOL_NAMES = {
    SEARCH_TOOL_NAME: "document search",
    REMEMBER_TOOL_NAME: "what the agent keeps about the user",
}


def _offered_tools(
    plugin: Plugin,
    context_source: ContextSource,
    top_k: int,
    memory: Memory | None,
) -> tuple[Tool, ...]:
    """A plugin with no memory slot behind it is offered no `remember`, so the
    absence is visible to the model rather than a tool that quietly forgets."""
    for tool in plugin.tools:
        if tool.name in RESERVED_TOOL_NAMES:
            raise ConfigurationError(
                f"A plugin tool may not be named '{tool.name}': that name belongs "
                f"to {RESERVED_TOOL_NAMES[tool.name]}."
            )
    remembering = (remember_tool(memory, _fact_rules()),) if memory is not None else ()
    return (search_tool(context_source, top_k), *remembering, *plugin.tools)


def _fact_rules() -> ValidationPipeline:
    """The core rules, sized for a fact, and no plugin rules: a plugin rule turns a
    *question* down on domain grounds, and a note about the user is not a question —
    the shipped medical filter would make "remember I have diabetes" unkeepable
    without closing anything."""
    return ValidationPipeline(
        core_rules=(
            EmptyInputRule("There was nothing to remember."),
            MaxLengthRule(
                MAX_FACT_CHARS,
                "That note is too long to keep — the limit is {limit} characters.",
            ),
            PromptInjectionRule(
                "That note reads as an attempt to change my instructions, "
                "so I have not kept it."
            ),
        ),
        plugin_rules=(),
    )


def build(config: Config, collection: str = DEFAULT_COLLECTION) -> App:
    from cora.adapters.bm25_keyword_index import Bm25KeywordIndex
    from cora.adapters.chroma_retriever import ChromaRetriever
    from cora.adapters.openrouter_chat_model import OpenRouterChatModel
    from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder
    from cora.adapters.sqlite_store_memory import SqliteStoreMemory

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
        memory=SqliteStoreMemory.at(config.memory_path),
        top_k=config.top_k,
        max_tool_rounds=config.max_tool_rounds,
        history_turns=config.history_turns,
        retrieval=config.retrieval,
        fusion_queries=config.fusion_queries,
        keyword_index=keyword_index,
        debug=config.debug,
    )
