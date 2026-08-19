import logging
from dataclasses import dataclass

from cora.adapters.langgraph_runner import langgraph_for
from cora.adapters.loaders import LOADERS
from cora.app.config import (
    DEFAULT_HISTORY_TURNS,
    DEFAULT_MAX_TOOL_ROUNDS,
    DEFAULT_TOP_K,
    Config,
)
from cora.app.log_config import enable_debug_logs
from cora.engine.agent import Agent
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.memory_tool import remember_tool
from cora.engine.plugin_registry import load_plugins
from cora.engine.plugin_set import PluginSet
from cora.engine.port_logging import (
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
)
from cora.engine.retrieval_tool import search_tool
from cora.engine.steps import ModelStep, PrepareStep, Router, ToolStep
from cora.engine.tool_runtime import ToolRuntime
from cora.ports.chat_model import ChatModel
from cora.ports.context_source import ContextSource
from cora.ports.conversations import Conversations
from cora.ports.documents import Documents
from cora.ports.embedding import Embedder
from cora.ports.graph import GraphFor
from cora.ports.memory import Memory
from cora.ports.plugin import Tool
from cora.ports.retrieval import Retriever

DEFAULT_COLLECTION = "documents"

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class App:
    agent: Agent
    knowledge_base: KnowledgeBase
    memory: Memory | None = None
    conversations: Conversations | None = None


def assemble(
    *,
    chat_model: ChatModel,
    embedder: Embedder,
    retriever: Retriever,
    documents: Documents,
    plugins: PluginSet,
    memory: Memory | None = None,
    conversations: Conversations | None = None,
    top_k: int = DEFAULT_TOP_K,
    max_tool_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
    history_turns: int = DEFAULT_HISTORY_TURNS,
    graph: GraphFor = langgraph_for,
    debug: bool = False,
) -> App:
    _announce(plugins)
    if debug:
        chat_model = LoggingChatModel(chat_model)
        embedder = LoggingEmbedder(embedder)
        retriever = LoggingRetriever(retriever)
    knowledge_base = KnowledgeBase(
        embedder=embedder, retriever=retriever, loaders=LOADERS, documents=documents
    )
    tools = _offered_tools(plugins, knowledge_base, top_k, memory)
    runner = graph(
        prepare=PrepareStep(
            rules=plugins.rules,
            instructions=plugins.instructions,
            memory=memory,
        ),
        model=ModelStep(
            chat_model=chat_model, tools=tools, max_history_turns=history_turns
        ).writing_to,
        tools=ToolStep(tool_runtime=ToolRuntime(tools=tools)),
        router=Router(max_tool_rounds=max_tool_rounds),
        max_tool_rounds=max_tool_rounds,
    )
    return App(
        agent=Agent(runner=runner, conversations=conversations),
        knowledge_base=knowledge_base,
        memory=memory,
        conversations=conversations,
    )


def _announce(plugins: PluginSet) -> None:
    """A screened app and an unscreened one are otherwise indistinguishable once
    running, so an unscreened one is a warning: it is the level that reaches the user
    without `CORA_DEBUG`, where the `cora` logger carries no handler. A bundle may
    contribute only tools, so what is announced is the screen, not the count."""
    if plugins.entries:
        log.info(
            "plugins loaded: %s", ", ".join(module for module, _ in plugins.entries)
        )
    if not any(plugin.validation_rules for _, plugin in plugins.entries):
        log.warning("no plugin screens what the user types")


def _offered_tools(
    plugins: PluginSet,
    context_source: ContextSource,
    top_k: int,
    memory: Memory | None,
) -> tuple[Tool, ...]:
    """No memory slot behind the app means no `remember` offered, so the absence is
    visible to the model rather than a tool that quietly forgets."""
    remembering = (remember_tool(memory),) if memory is not None else ()
    return (search_tool(context_source, top_k), *remembering, *plugins.tools)


def build(config: Config, collection: str = DEFAULT_COLLECTION) -> App:
    from functools import partial

    from cora.adapters.chroma_retriever import ChromaRetriever
    from cora.adapters.openrouter_chat_model import OpenRouterChatModel
    from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder
    from cora.adapters.sqlite_conversations import SqliteConversations
    from cora.adapters.sqlite_documents import SqliteDocuments
    from cora.adapters.sqlite_store_memory import SqliteStoreMemory

    enable_debug_logs(config.debug, config.log_path)
    retriever = ChromaRetriever(path=config.db_path, collection=collection)
    return assemble(
        chat_model=OpenRouterChatModel(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            max_output_tokens=config.max_output_tokens,
            request_timeout_seconds=config.request_timeout_seconds,
            reasoning_effort=config.reasoning_effort,
        ),
        embedder=SentenceTransformerEmbedder(),
        retriever=retriever,
        documents=SqliteDocuments.at(config.documents_path),
        plugins=load_plugins(config.plugin_modules),
        memory=SqliteStoreMemory.at(config.memory_path),
        conversations=SqliteConversations.at(config.conversations_path),
        graph=partial(langgraph_for, checkpoints_at=config.conversations_path),
        top_k=config.top_k,
        max_tool_rounds=config.max_tool_rounds,
        history_turns=config.history_turns,
        debug=config.debug,
    )
