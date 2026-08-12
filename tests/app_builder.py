"""Assembled apps for tests. Apart from `fakes`, which the engine and adapter suites
import and which therefore may not depend on the composition root."""

from typing import Any

from cora.app.assembly import App, assemble
from cora.engine.plugin_set import PluginSet
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.embedding import Embedder
from cora.ports.plugin import Plugin
from cora.ports.retrieval import Retriever
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin

FIXTURE_MODULE = "fixture_plugins.valid"


def assembled(
    *,
    chat_model: ChatModel | None = None,
    embedder: Embedder | None = None,
    retriever: Retriever | None = None,
    plugin: Plugin | None = None,
    plugins: PluginSet | None = None,
    **overrides: Any,
) -> App:
    """`plugin` is the one-plugin shorthand most tests want; `plugins` takes a whole
    composed set, and `PluginSet()` asks for bare cora."""
    if plugins is None:
        plugins = PluginSet(((FIXTURE_MODULE, plugin or make_plugin()),))
    return assemble(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text="ok")]),
        embedder=embedder or FakeEmbedder(),
        retriever=retriever or FakeRetriever(),
        plugins=plugins,
        **overrides,
    )


def indexed(app: App, *docs: tuple[str, bytes]) -> App:
    for filename, data in docs:
        app.knowledge_base.add_file(data, filename)
    return app
