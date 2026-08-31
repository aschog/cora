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
)
from cora.app.config import (
    plugin_settings as read_plugin_settings,
)
from cora.app.log_config import enable_debug_logs
from cora.domain.errors import PluginLoadError
from cora.engine.agent import Agent
from cora.engine.ask_tool import ask_tool
from cora.engine.host import PluginHost
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.memory_tool import remember_tool
from cora.engine.plugin_registry import load_plugins
from cora.engine.plugin_set import Registry
from cora.engine.port_logging import (
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
)
from cora.engine.retrieval_tool import search_tool
from cora.engine.steps import (
    ANSWER,
    FOCUS,
    ROUTE,
    SCREEN,
    WORK,
    AnswerStep,
    AskStep,
    FocusStep,
    ModelStep,
    Named,
    Router,
    RouteStep,
    ScreenStep,
    ToolStep,
)
from cora.engine.tool_runtime import ToolRuntime
from cora.engine.validation import CORA
from cora.engine.validation import extend as coras_own_screen
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
    scopes: tuple[str, ...] = (),
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
        plugin_settings: What each plugin module may read as its own settings, keyed
            by module path. A deployment fills this from the environment.
        scopes: The fields a turn may run under — which of the plugins' scoped
            registrations this deployment offers. Naming one leaves the routing step
            nothing to choose between; naming two is what it chooses between.
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
    _announce(plugins)
    registry = _registered(
        plugins,
        documents=knowledge_base,
        model=chat_model,
        memory=memory,
        settings=plugin_settings or {},
        top_k=top_k,
    )
    _warn_unscreened(registry)
    tools = _coras_own_tools(knowledge_base, top_k, memory)
    runner = graph(
        before=(
            Named(SCREEN, ScreenStep(registry=registry)),
            Named(
                ROUTE,
                RouteStep(chat_model=chat_model, available=scopes, registry=registry),
            ),
            Named(
                FOCUS,
                FocusStep(registry=registry, memory=memory, pause=interrupting),
            ),
        ),
        loop=Loop(
            marker=Named(WORK),
            model=ModelStep(
                chat_model=chat_model,
                tools=tools,
                max_history_turns=history_turns,
                registry=registry,
            ).writing_to,
            tools=ToolStep(
                tool_runtime=ToolRuntime(tools=tools, registry=registry),
                registry=registry,
            ),
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


def _announce(plugins: tuple[Extension, ...]) -> None:
    """Say in the log what loaded, before any of it is asked to register.

    Ahead of registering rather than after it, so a plugin that fails to register is
    read against the list it was named in — an operator debugging a refusal is owed
    what else was loaded. What loaded is what the deployment named, not what
    registered: a plugin that registered nothing is the one they most need to see.
    """
    if plugins:
        log.info("plugins loaded: %s", ", ".join(plugin.module for plugin in plugins))


def _warn_unscreened(registry: Registry) -> None:
    """Warn when nothing a plugin registered screens the user's input.

    A screened app and an unscreened one are otherwise indistinguishable once running,
    so an unscreened one is a warning: it is the level that reaches the user without
    `CORA_DEBUG`, where the `cora` logger carries no handler. A plugin may register
    only tools, so what is announced is the screen, not the count.
    """
    if not registry.screened_by_a_plugin():
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

    Cora registers first, under its own name: its screen is a subscriber like any
    other, and being first is what "cora's screen runs first" is made of.

    Raises:
        PluginLoadError: A plugin raised while registering. The module is named, and
            the turn it would have served never starts.
        ConfigurationError: What they registered cannot be composed.
    """
    entries = []
    for plugin in (Extension(module=CORA, extend=coras_own_screen), *plugins):
        host = PluginHost(
            module=plugin.module,
            index=documents,
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


def _coras_own_tools(
    context_source: ContextSource,
    top_k: int,
    memory: Memory | None,
) -> tuple[Tool, ...]:
    """What every turn may call, whatever it is running under.

    The plugins' tools are not here: which of them a turn may call depends on its
    scopes, so they are read off the registry per turn rather than fixed at assembly.
    No memory slot behind the app means no `remember` offered, so the absence is visible
    to the model rather than a tool that quietly forgets.
    """
    remembering = (remember_tool(memory),) if memory is not None else ()
    return (search_tool(context_source, top_k), *remembering, ask_tool())


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
        plugin_settings=read_plugin_settings(config.plugin_modules),
        scopes=config.scopes,
        memory=SqliteStoreMemory.at(config.memory_path),
        conversations=SqliteConversations.at(config.conversations_path),
        graph=partial(langgraph_for, checkpoints_at=config.conversations_path),
        top_k=config.top_k,
        max_tool_rounds=config.max_tool_rounds,
        history_turns=config.history_turns,
        debug=config.debug,
    )
