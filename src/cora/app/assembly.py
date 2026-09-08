"""Where the ports are filled and the agent is put together."""

import logging
import pathlib
import threading
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from cora.adapters.langgraph_runner import interrupting, langgraph_for, saver_at
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
from cora.domain.errors import PluginLoadError, PluginRemovalError
from cora.engine.agent import Agent
from cora.engine.ask_tool import ask_for_tool, ask_tool
from cora.engine.host import PluginHost
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.memory_tool import remember_tool
from cora.engine.plugin_registry import folder_signature, load_plugins
from cora.engine.plugin_set import Registry
from cora.engine.port_logging import (
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
)
from cora.engine.removal import NO_FOLDER, remove_plugin
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
    GateStep,
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
from cora.ports.host import Extension, Listed
from cora.ports.memory import Memory
from cora.ports.output import Output
from cora.ports.plugin import Tool
from cora.ports.retrieval import Retriever

log = logging.getLogger(__name__)


def _nothing_to_delete(name: str) -> None:
    """What an app composed without a plugins folder answers a delete with."""
    raise PluginRemovalError(name, NO_FOLDER)


@dataclass(frozen=True)
class App:
    """Everything a frontend is handed: an agent to ask, and the stores behind it.

    `memory` and `conversations` are optional because an app can run without either —
    what is missing is then missing from the page too, rather than faked.

    `scopes` is the fields this composition offers: what was configured, plus every
    field a loaded plugin registered. The page reads it off the app, because with a
    live plugins folder it is the composition's fact, not a setting's.

    `remove` deletes one dropped plugin and the data of the fields it brought. Bound
    to this composition, because what a plugin brought is what this composition
    loaded — a caller names the plugin and nothing else. `plugins_folder` is where a
    plugin can be deleted from, which is what says whether one is deletable at all,
    and `configured` is the fields the deployment named itself, which no plugin's
    deletion empties.
    """

    agent: Agent
    knowledge_base: KnowledgeBase
    plugins: tuple[Listed, ...] = ()
    memory: Memory | None = None
    conversations: Conversations | None = None
    scopes: tuple[str, ...] = ()
    configured: tuple[str, ...] = ()
    plugins_folder: pathlib.Path | None = None
    remove: Callable[[str], None] = _nothing_to_delete


class LiveApp:
    """The plugins folder made live: one composition at a time, over parts made once.

    `compose` closes over everything that outlives a folder change — the adapters and
    the deployment's own settings — and what the folder holds is re-read and composed
    through it. The named modules ride along on every composition, which Python's
    module cache makes the same objects each time: only the folder moves. The first
    composition happens here, so a deployment that cannot start is refused at start.
    """

    def __init__(
        self,
        *,
        compose: Callable[[tuple[Extension, ...]], App],
        named: tuple[str, ...] = (),
        folder: pathlib.Path | None = None,
    ) -> None:
        """Composes once, here: a folder that cannot load refuses the start itself.

        Args:
            compose: An app from the plugins handed to it; everything else it needs
                is its own, made once and reused across compositions.
            named: The module paths the deployment configured, loaded every
                composition and cached by Python into the same modules.
            folder: Where plugins are dropped. Absent, the folder simply never moves.
        """
        self._compose = compose
        self._named = named
        self._folder = folder
        self._lock = threading.Lock()
        self._signature = folder_signature(folder)
        self._app = self._composed()

    def current(self) -> App:
        """The app the folder describes right now.

        Composed again only when the folder moved since the last look — a stat scan,
        cheap enough to pay per request. A reader keeps whatever app it already took,
        so a turn runs whole on the set it started with.

        Raises:
            PluginLoadError: What the folder now holds cannot be loaded. The last
                composition stands, this read is refused, and the next one retries.
            ConfigurationError: What it holds cannot be composed together; the same
                standing applies.
        """
        with self._lock:
            signature = folder_signature(self._folder)
            if signature != self._signature:
                self._app = self._composed()
                self._signature = signature
            return self._app

    def _composed(self) -> App:
        return self._compose(load_plugins(self._named, folder=self._folder))


def assemble(
    *,
    chat_model: ChatModel,
    embedder: Embedder,
    retriever: Retriever,
    documents: Documents,
    plugins: tuple[Extension, ...] = (),
    plugin_settings: dict[str, dict[str, str]] | None = None,
    scopes: tuple[str, ...] = (),
    plugins_folder: pathlib.Path | None = None,
    memory: Memory | None = None,
    conversations: Conversations | None = None,
    output: Output | None = None,
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
        scopes: Fields the deployment names beyond what its plugins register — the
            way a documents-only field exists. What a turn may run under is these
            plus every field a loaded plugin registered: loading a plugin is the
            deployment act, and its fields come with it.
        plugins_folder: Where plugins are dropped, which is the only place one can be
            deleted from. The same path the plugins were loaded from: a plugin is
            matched against it as it was found, so any other path leaves every plugin
            undeletable. Without it a deployment has no plugin it can delete.
        memory: What cora keeps about the user. Without it, no `remember` tool is
            offered at all.
        conversations: Where turns are recorded. Without it, a turn is answered and
            not kept.
        output: Where an approved effect writes what it produced. Without it, a plugin
            whose tool needs one registers no such tool.
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
        output=output,
        settings=plugin_settings or {},
        top_k=top_k,
    )
    _warn_unscreened(registry)
    offered = _offered(scopes, registry)
    tools = _coras_own_tools(knowledge_base, top_k, memory)
    runner = graph(
        before=(
            Named(SCREEN, ScreenStep(registry=registry)),
            Named(
                ROUTE,
                RouteStep(chat_model=chat_model, available=offered, registry=registry),
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
            gate=GateStep(tools=tools, registry=registry, approve=interrupting),
            tools=ToolStep(
                tool_runtime=ToolRuntime(tools=tools, registry=registry),
                registry=registry,
            ),
            ask=AskStep(pause=interrupting),
            router=Router(max_tool_rounds=max_tool_rounds),
        ),
        after=(Named(ANSWER, AnswerStep(registry=registry)),),
        max_tool_rounds=max_tool_rounds,
    )
    agent = Agent(runner=runner, conversations=conversations)
    listing = registry.listing(plugins)
    return App(
        agent=agent,
        knowledge_base=knowledge_base,
        plugins=listing,
        memory=memory,
        conversations=conversations,
        scopes=offered,
        configured=scopes,
        plugins_folder=plugins_folder,
        remove=partial(
            remove_plugin,
            folder=plugins_folder,
            listing=listing,
            configured=scopes,
            knowledge_base=knowledge_base,
            agent=agent,
        ),
    )


def _offered(scopes: tuple[str, ...], registry: Registry) -> tuple[str, ...]:
    """The configured fields, then everything the loaded plugins registered under.

    One rule for a field: it is offered because something brings it. Sorted past the
    configured ones and each named once — a field is a field, however many
    registrations carry it.
    """
    brought = sorted(
        {entry.scope for entry in registry.entries if entry.scope is not None}
    )
    return (*scopes, *(scope for scope in brought if scope not in scopes))


def _announce(plugins: tuple[Extension, ...]) -> None:
    """Say in the log what loaded, before any of it is asked to register.

    Ahead of registering rather than after it, so a plugin that fails to register is
    read against the list it was named in — an operator debugging a refusal is owed
    what else was loaded. What loaded is what the deployment named, not what
    registered: a plugin that registered nothing is the one they most need to see.
    """
    if plugins:
        log.info("plugins loaded: %s", ", ".join(plugin.source for plugin in plugins))


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
    output: Output | None,
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
            output=output,
            settings=settings.get(plugin.module, {}),
            top_k=top_k,
        )
        try:
            plugin.extend(host)
        except PluginLoadError:
            raise
        except Exception as failed:
            raise PluginLoadError(
                plugin.source,
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
    return (
        search_tool(context_source, top_k),
        *remembering,
        ask_tool(),
        ask_for_tool(),
    )


def build(config: Config) -> App:
    """The real app: every slot filled from configuration, ready to answer.

    Raises:
        AdapterError: A store could not be opened.
        PluginLoadError: A plugin named in the configuration could not be loaded.
        ConfigurationError: The plugins load but cannot be composed together.
    """
    folder = _folder_of(config)
    return _composer(config, folder)(load_plugins(config.plugin_modules, folder=folder))


def live(config: Config) -> LiveApp:
    """The real app served live: `build`'s slots, composed again as the folder moves.

    Raises:
        AdapterError: A store could not be opened.
        PluginLoadError: A plugin named in the configuration could not be loaded.
        ConfigurationError: The plugins load but cannot be composed together.
    """
    folder = _folder_of(config)
    return LiveApp(
        compose=_composer(config, folder),
        named=config.plugin_modules,
        folder=folder,
    )


def _folder_of(config: Config) -> pathlib.Path:
    folder = pathlib.Path(config.plugins_path).resolve()
    log.info("reading dropped plugins from %s", folder)
    return folder


def _composer(
    config: Config, folder: pathlib.Path
) -> Callable[[tuple[Extension, ...]], App]:
    """Every slot that outlives a folder change, filled once and closed over.

    The adapters are imported here rather than at the top, so importing `cora.app` costs
    nothing a frontend does not use — the embedding model in particular is loaded on
    first use, not on import.

    Raises:
        AdapterError: A store could not be opened.
    """
    from cora.adapters.file_documents import FileDocuments
    from cora.adapters.file_output import FileOutput
    from cora.adapters.openrouter_chat_model import OpenRouterChatModel
    from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder
    from cora.adapters.sqlite_conversations import SqliteConversations
    from cora.adapters.sqlite_store_memory import SqliteStoreMemory
    from cora.adapters.sqlite_vec_retriever import SqliteVecRetriever

    enable_debug_logs(config.debug, config.log_path)
    chat_model = OpenRouterChatModel(
        model=config.model,
        api_key=config.api_key,
        base_url=config.base_url,
        max_output_tokens=config.max_output_tokens,
        request_timeout_seconds=config.request_timeout_seconds,
        reasoning_effort=config.reasoning_effort,
    )
    embedder = SentenceTransformerEmbedder()
    retriever = SqliteVecRetriever.at(config.db_path)
    documents = FileDocuments.at(config.documents_path)
    memory = SqliteStoreMemory.at(config.db_path)
    conversations = SqliteConversations.at(config.db_path)
    output = FileOutput.at(config.output_path)
    # The checkpointer is an adapter like the stores above it: made once, so a folder
    # change recomposes over the same connection instead of opening another onto the
    # same store file.
    graph = partial(langgraph_for, checkpointer=saver_at(config.db_path))

    def compose(loaded: tuple[Extension, ...]) -> App:
        # Settings read off what loaded rather than off what the deployment typed: a
        # plugin dropped in the folder was named by nobody, and settings keyed by
        # `CORA_PLUGINS` would hand it an empty slice under a name it does not have.
        return assemble(
            chat_model=chat_model,
            embedder=embedder,
            retriever=retriever,
            documents=documents,
            plugins=loaded,
            plugin_settings=read_plugin_settings(
                tuple(plugin.module for plugin in loaded)
            ),
            scopes=config.scopes,
            plugins_folder=folder,
            memory=memory,
            conversations=conversations,
            output=output,
            graph=graph,
            top_k=config.top_k,
            max_tool_rounds=config.max_tool_rounds,
            history_turns=config.history_turns,
            debug=config.debug,
        )

    return compose
