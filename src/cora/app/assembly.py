from dataclasses import dataclass

from cora.adapters.port_logging import (
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
)
from cora.app.config import DEFAULT_MAX_TOOL_ROUNDS, DEFAULT_TOP_K, Config
from cora.core.ports.chat_model import ChatModel
from cora.core.ports.embedding import Embedder
from cora.core.ports.plugin import Plugin
from cora.core.ports.retrieval import Retriever
from cora.core.services.chat_engine import ChatEngine
from cora.core.services.knowledge_base import KnowledgeBase
from cora.core.services.plugin_registry import load_plugin
from cora.core.services.tool_runtime import ToolRuntime
from cora.core.services.validation import (
    EmptyInputRule,
    MaxLengthRule,
    ValidationPipeline,
)

MAX_INPUT_CHARS = 4000
DEFAULT_DB_PATH = ".cora/chroma"
DEFAULT_COLLECTION = "documents"


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
    debug: bool = False,
) -> App:
    if debug:
        chat_model = LoggingChatModel(chat_model)
        embedder = LoggingEmbedder(embedder)
        retriever = LoggingRetriever(retriever)
    knowledge_base = KnowledgeBase(embedder=embedder, retriever=retriever)
    for filename, data in plugin.seed_docs:
        knowledge_base.add_file(data, filename)
    validation = ValidationPipeline(
        core_rules=(EmptyInputRule(), MaxLengthRule(MAX_INPUT_CHARS)),
        plugin_rules=plugin.validation_rules,
    )
    engine = ChatEngine(
        chat_model=chat_model,
        knowledge_base=knowledge_base,
        validation=validation,
        tool_runtime=ToolRuntime(tools=plugin.tools),
        top_k=top_k,
        max_tool_rounds=max_tool_rounds,
        system_prompt=plugin.system_prompt,
        tools=plugin.tools,
    )
    return App(engine=engine, knowledge_base=knowledge_base)


def build(
    config: Config,
    db_path: str = DEFAULT_DB_PATH,
    collection: str = DEFAULT_COLLECTION,
) -> App:
    from cora.adapters.chroma_retriever import ChromaRetriever
    from cora.adapters.openrouter_chat_model import OpenRouterChatModel
    from cora.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder

    return assemble(
        chat_model=OpenRouterChatModel(
            model=config.model, api_key=config.api_key, base_url=config.base_url
        ),
        embedder=SentenceTransformerEmbedder(),
        retriever=ChromaRetriever(path=db_path, collection=collection),
        plugin=load_plugin(config.plugin_module),
        top_k=config.top_k,
        max_tool_rounds=config.max_tool_rounds,
    )
