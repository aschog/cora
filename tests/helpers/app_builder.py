from typing import Any

from cora.app.assembly import App, assemble
from cora.engine.plugin_registry import load_plugin
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.documents import Documents
from cora.ports.embedding import Embedder
from cora.ports.host import DEFAULT_SCOPE, Extension
from cora.ports.retrieval import Retriever
from fakes import (
    FakeDocuments,
    FakeEmbedder,
    FakeFiles,
    FakeRetriever,
    ScriptedChatModel,
)
from fixture_plugins import make_plugin

FIXTURE_MODULE = "fixture_plugins.valid"
# The shipped plugin that lets cora stop and ask, loaded ahead of whatever a test
# brings where the test says `asking=True`: cora alone no longer has a card of its own
# to put, and a test about the fork or the form is a test with this plugin loaded.
ASKING = load_plugin("cora.plugins.ask")
# The shipped plugin that indexes an upload and searches the field, loaded unless a test
# says `searching=False`: a document that can be searched and cited is what most of the
# suite uploads for, and cora alone keeps the file and does nothing with it.
SEARCHING = load_plugin("cora.plugins.documents")


def shipped(*names: str) -> tuple[Extension, ...]:
    return tuple(load_plugin(f"cora.plugins.{name}") for name in names)


def assembled(
    *,
    chat_model: ChatModel | None = None,
    embedder: Embedder | None = None,
    retriever: Retriever | None = None,
    documents: Documents | None = None,
    plugin: Extension | None = None,
    plugins: tuple[Extension, ...] | None = None,
    asking: bool = False,
    searching: bool = True,
    **overrides: Any,
) -> App:
    if plugins is None:
        plugins = (plugin or make_plugin(),)
    if asking:
        plugins = (ASKING, *plugins)
    if searching:
        plugins = (SEARCHING, *plugins)
    overrides.setdefault("files", FakeFiles())
    return assemble(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text="ok")]),
        embedder=embedder or FakeEmbedder(),
        retriever=retriever or FakeRetriever(),
        documents=documents or FakeDocuments(),
        plugins=plugins,
        **overrides,
    )


def indexed(app: App, *docs: tuple[str, bytes], scope: str = DEFAULT_SCOPE) -> App:
    assert app.intake is not None
    for filename, data in docs:
        app.intake.take(scope, filename, data)
    return app
