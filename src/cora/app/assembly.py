"""Where the ports are filled and the agent is put together."""

import logging
from dataclasses import dataclass

from cora.adapters.langgraph_runner import interrupting, langgraph_for
from cora.adapters.loaders import LOADERS
from cora.app.config import (
    DEFAULT_HISTORY_TURNS,
    DEFAULT_MAX_TOOL_ROUNDS,
    DEFAULT_TOP_K,
    Config,
    plugin_settings,
)
from cora.app.log_config import enable_debug_logs
from cora.domain.errors import PluginLoadError
from cora.engine.agent import Agent
from cora.engine.ask_tool import ask_tool
from cora.engine.host import PluginHost
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.memory_tool import remember_tool
from cora.engine.plugin_registry import load_plugins
from cora.engine.plugin_set import CORA_RULES, Registry
from cora.engine.port_logging import (
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
)
from cora.engine.retrieval_tool import search_tool
from cora.engine.steps import (
    ANSWER,
    SCREEN,
    WORK,
    AnswerStep,
    AskStep,
    ModelStep,
    Named,
    Router,
    ScreenStep,
    ToolStep,
)
from cora.engine.tool_runtime import ToolRuntime
from cora.ports.chat_model import ChatModel
from cora.ports.context_source import ContextSource
from cora.ports.conversations import Conversations
from cora.ports.documents import Documents
from cora.ports.embedding import Embedder
from cora.ports.graph import GraphFor, Loop
from cora.ports.host import Extension
from cora.ports.memory import Memory
from cora.ports.plugin import Tool
from cora.ports.retrieval import Retriever

DEFAULT_COLLECTION = "documents"

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class App:
    """Everything a frontend is handed: an agent to ask, and the stores behind it.

    `memory` and `conversations` are optional because an app can run without either —
    what is missing is then missing from the page too, rather than faked.
    """

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
    plugins: tuple[Extension, ...] = (),
    plugin_settings: dict[str, dict[str, str]] | None = None,
    memory: Memory | None = None,
    conversations: Conversations | None = None,
    top_k: int = DEFAULT_TOP_K,
    max_tool_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
    history_turns: int = DEFAULT_HISTORY_TURNS,
    graph: GraphFor = langgraph_for,
    debug: bool = False,
) -> App:
    """Put an app together from the slots given, and offer the tools they imply.

    Args:
        chat_model: The model behind every turn.
        embedder: Embeds both the chunks and the queries; one embedder for both, or
            neither side is comparable.
        retriever: The index the chunks go into.
        documents: Where the text a citation opens onto is kept.
        plugins: The plugin modules cora was asked for, already imported. Each is
            handed a host of its own and registers what it has.
        plugin_settings: What each plugin module may read as its own settings, keyed by
            module path. A deployment fills this from the environment.
        memory: What cora keeps about the user. Without it, no `remember` tool is
            offered at all.
        conversations: Where turns are recorded. Without it, a turn is answered and
            not kept.
        top_k: How many passages a document search returns.
        max_tool_rounds: How many rounds of tools one turn may spend.
        history_turns: How many earlier turns of the thread reach the prompt.
        graph: Which engine walks the steps; LangGraph unless a test says otherwise.
        debug: Wraps the three outward ports in logging ones.
    """
    if debug:
        chat_model = LoggingChatModel(chat_model)
        embedder = LoggingEmbedder(embedder)
        retriever = LoggingRetriever(retriever)
    knowledge_base = KnowledgeBase(
        embedder=embedder, retriever=retriever, loaders=LOADERS, documents=documents
    )
    registry = _registered(
        plugins,
        documents=knowledge_base,
        model=chat_model,
        memory=memory,
        settings=plugin_settings or {},
        top_k=top_k,
    )
    _announce(plugins, registry)
    tools = _offered_tools(registry, knowledge_base, top_k, memory)
    runner = graph(
        before=(
            Named(
                SCREEN,
                ScreenStep(
                    rules=registry.rules,
                    instructions=registry.instructions,
                    memory=memory,
                ),
            ),
        ),
        loop=Loop(
            marker=Named(WORK),
            model=ModelStep(
                chat_model=chat_model, tools=tools, max_history_turns=history_turns
            ).writing_to,
            tools=ToolStep(tool_runtime=ToolRuntime(tools=tools)),
            ask=AskStep(pause=interrupting),
            router=Router(max_tool_rounds=max_tool_rounds),
        ),
        after=(Named(ANSWER, AnswerStep()),),
        max_tool_rounds=max_tool_rounds,
    )
    return App(
        agent=Agent(runner=runner, conversations=conversations),
        knowledge_base=knowledge_base,
        memory=memory,
        conversations=conversations,
    )


def _announce(plugins: tuple[Extension, ...], registry: Registry) -> None:
    """Say in the log what loaded, and warn when nothing screens the user's input.

    A screened app and an unscreened one are otherwise indistinguishable once running,
    so an unscreened one is a warning: it is the level that reaches the user without
    `CORA_DEBUG`, where the `cora` logger carries no handler. A plugin may register
    only tools, so what is announced is the screen, not the count. What loaded is what
    the deployment named, not what registered: a plugin that registered nothing is the
    one an operator most needs to see.
    """
    if plugins:
        log.info("plugins loaded: %s", ", ".join(plugin.module for plugin in plugins))
    if len(registry.rules) == len(CORA_RULES):
        log.warning("no plugin screens what the user types")


def _registered(
    plugins: tuple[Extension, ...],
    *,
    documents: ContextSource,
    model: ChatModel,
    memory: Memory | None,
    settings: dict[str, dict[str, str]],
    top_k: int,
) -> Registry:
    """Hand each plugin a host of its own, and keep what it registered.

    Registering is what loading could not do: a host is made of the parts assembled
    here, so `extend` is called now rather than when the module was imported.

    Raises:
        PluginLoadError: A plugin raised while registering. The module is named, and
            the turn it would have served never starts.
        ConfigurationError: What they registered cannot be composed.
    """
    entries = []
    for plugin in plugins:
        host = PluginHost(
            module=plugin.module,
            documents=documents,
            model=model,
            memory=memory,
            settings=settings.get(plugin.module, {}),
            top_k=top_k,
        )
        try:
            plugin.extend(host)
        except PluginLoadError:
            raise
        except Exception as failed:
            raise PluginLoadError(
                plugin.module,
                f"the plugin raised {type(failed).__name__} while registering",
            ) from failed
        entries.extend(host.registered)
    return Registry(tuple(entries))


def _offered_tools(
    registry: Registry,
    context_source: ContextSource,
    top_k: int,
    memory: Memory | None,
) -> tuple[Tool, ...]:
    """What the model may call, cora's own tools first and the plugins' after.

    No memory slot behind the app means no `remember` offered, so the absence is visible
    to the model rather than a tool that quietly forgets.
    """
    remembering = (remember_tool(memory),) if memory is not None else ()
    return (
        search_tool(context_source, top_k),
        *remembering,
        ask_tool(),
        *registry.tools,
    )


def build(config: Config, collection: str = DEFAULT_COLLECTION) -> App:
    """The real app: every slot filled from configuration, ready to answer.

    The adapters are imported here rather than at the top, so importing `cora.app` costs
    nothing a frontend does not use — the embedding model in particular is loaded on
    first use, not on import.

    Raises:
        AdapterError: A store could not be opened.
        PluginLoadError: A plugin named in the configuration could not be loaded.
        ConfigurationError: The plugins load but cannot be composed together.
    """
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
        plugin_settings=plugin_settings(config.plugin_modules),
        memory=SqliteStoreMemory.at(config.memory_path),
        conversations=SqliteConversations.at(config.conversations_path),
        graph=partial(langgraph_for, checkpoints_at=config.conversations_path),
        top_k=config.top_k,
        max_tool_rounds=config.max_tool_rounds,
        history_turns=config.history_turns,
        debug=config.debug,
    )
