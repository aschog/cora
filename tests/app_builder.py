"""Assembled apps for tests. Apart from `fakes`, which the engine and adapter suites
import and which therefore may not depend on the composition root."""

from typing import Any

from cora.app.assembly import App, assemble
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.embedding import Embedder
from cora.ports.plugin import Plugin
from cora.ports.retrieval import Retriever
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin


def assembled(
    *,
    chat_model: ChatModel | None = None,
    embedder: Embedder | None = None,
    retriever: Retriever | None = None,
    plugin: Plugin | None = None,
    **overrides: Any,
) -> App:
    return assemble(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text="ok")]),
        embedder=embedder or FakeEmbedder(),
        retriever=retriever or FakeRetriever(),
        plugin=plugin or make_plugin(),
        **overrides,
    )


def indexed(app: App, *docs: tuple[str, bytes]) -> App:
    for filename, data in docs:
        app.knowledge_base.add_file(data, filename)
    return app
