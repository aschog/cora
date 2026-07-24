from cora.config import DEFAULT_MAX_TOOL_ROUNDS, DEFAULT_TOP_K, Config
from core.ports.chat_model import ChatModel
from core.ports.embedding import Embedder
from core.ports.plugin import Plugin
from core.ports.retrieval import Retriever
from core.services.chat_engine import ChatEngine
from core.services.knowledge_base import KnowledgeBase
from core.services.plugin_registry import load_plugin
from core.services.tool_runtime import ToolRuntime
from core.services.validation import EmptyInputRule, MaxLengthRule, ValidationPipeline

MAX_INPUT_CHARS = 4000
DEFAULT_DB_PATH = ".cora/chroma"
DEFAULT_COLLECTION = "documents"


def assemble(
    *,
    chat_model: ChatModel,
    embedder: Embedder,
    retriever: Retriever,
    plugin: Plugin,
    top_k: int = DEFAULT_TOP_K,
    max_tool_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
) -> ChatEngine:
    knowledge_base = KnowledgeBase(embedder=embedder, retriever=retriever)
    for filename, data in plugin.seed_docs:
        knowledge_base.add_file(data, filename)
    validation = ValidationPipeline(
        core_rules=(EmptyInputRule(), MaxLengthRule(MAX_INPUT_CHARS)),
        plugin_rules=plugin.validation_rules,
    )
    return ChatEngine(
        chat_model=chat_model,
        knowledge_base=knowledge_base,
        validation=validation,
        tool_runtime=ToolRuntime(tools=plugin.tools),
        top_k=top_k,
        max_tool_rounds=max_tool_rounds,
        system_prompt=plugin.system_prompt,
        tools=plugin.tools,
    )


def build_engine(
    config: Config,
    db_path: str = DEFAULT_DB_PATH,
    collection: str = DEFAULT_COLLECTION,
) -> ChatEngine:
    from core.adapters.chroma_retriever import ChromaRetriever
    from core.adapters.openrouter_chat_model import OpenRouterChatModel
    from core.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder

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
