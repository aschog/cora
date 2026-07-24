from cora.config import DEFAULT_MAX_TOOL_ROUNDS, DEFAULT_TOP_K
from core.chat_engine import ChatEngine
from core.chat_model import ChatModel
from core.embedding import Embedder
from core.knowledge_base import KnowledgeBase
from core.plugin import Plugin
from core.retrieval import Retriever
from core.tool_runtime import ToolRuntime
from core.validation import EmptyInputRule, MaxLengthRule, ValidationPipeline

MAX_INPUT_CHARS = 4000


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
