from typing import Any

from cora.app.assembly import App, assemble
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.documents import Documents
from cora.ports.embedding import Embedder
from cora.ports.host import DEFAULT_SCOPE, Extension
from cora.ports.retrieval import Retriever
from fakes import FakeDocuments, FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin

FIXTURE_MODULE = "fixture_plugins.valid"


def assembled(
    *,
    chat_model: ChatModel | None = None,
    embedder: Embedder | None = None,
    retriever: Retriever | None = None,
    documents: Documents | None = None,
    plugin: Extension | None = None,
    plugins: tuple[Extension, ...] | None = None,
    **overrides: Any,
) -> App:
    if plugins is None:
        plugins = (plugin or make_plugin(),)
    return assemble(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text="ok")]),
        embedder=embedder or FakeEmbedder(),
        retriever=retriever or FakeRetriever(),
        documents=documents or FakeDocuments(),
        plugins=plugins,
        **overrides,
    )


def indexed(app: App, *docs: tuple[str, bytes], scope: str = DEFAULT_SCOPE) -> App:
    for filename, data in docs:
        app.knowledge_base.add_file(data, filename, scope)
    return app
