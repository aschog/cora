from pathlib import Path

import pytest

from cora.app.assembly import App, assemble, build
from cora.app.config import Config
from cora.core.errors import InputRejectedError
from cora.core.ports.chat_model import ModelReply
from cora.core.ports.plugin import Plugin
from cora.core.services.chat_engine import ChatEngine
from cora.core.services.plugin_registry import load_plugin
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin


def _assemble(
    plugin: Plugin,
    *,
    chat_model: ScriptedChatModel | None = None,
    retriever: FakeRetriever | None = None,
) -> App:
    return assemble(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text="ok")]),
        embedder=FakeEmbedder(),
        retriever=retriever or FakeRetriever(),
        plugin=plugin,
    )


def test_assemble_returns_app_exposing_engine_and_knowledge_base() -> None:
    plugin = make_plugin(seed_docs=(("note.md", b"protein supports muscle growth"),))

    app = assemble(
        chat_model=ScriptedChatModel([ModelReply(text="42")]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        plugin=plugin,
    )

    assert isinstance(app, App)
    assert app.engine.answer("What is the answer?").answer == "42"
    assert "note.md" in app.knowledge_base.list_sources()


def test_assemble_answers_a_happy_path_question() -> None:
    app = _assemble(
        make_plugin(), chat_model=ScriptedChatModel([ModelReply(text="42")])
    )

    result = app.engine.answer("What is the answer?")

    assert result.answer == "42"


def test_assemble_seeds_plugin_docs_into_the_knowledge_base() -> None:
    plugin = make_plugin(seed_docs=(("note.md", b"protein supports muscle growth"),))
    retriever = FakeRetriever()

    _assemble(plugin, retriever=retriever)

    assert "note.md" in retriever.sources()


class _RejectBanned:
    def apply(self, user_input: str) -> None:
        if "banned" in user_input:
            raise InputRejectedError("No banned words, please.")


def test_assemble_chains_core_and_plugin_validation_rules() -> None:
    app = _assemble(make_plugin(validation_rules=(_RejectBanned(),)))

    with pytest.raises(InputRejectedError):
        app.engine.answer("   ")  # core rule: empty input

    with pytest.raises(InputRejectedError):
        app.engine.answer("a banned word")  # plugin rule


@pytest.mark.integration
def test_build_wires_real_adapters_from_config(tmp_path: Path) -> None:
    config = Config(
        api_key="k",
        model="openai/gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",
        plugin_module="fixture_plugins.valid",
        top_k=3,
        max_tool_rounds=4,
    )

    app = build(config, db_path=str(tmp_path))

    plugin = load_plugin("fixture_plugins.valid")
    assert isinstance(app, App)
    assert app.knowledge_base is app.engine.knowledge_base
    engine = app.engine
    assert isinstance(engine, ChatEngine)
    assert engine.system_prompt == plugin.system_prompt
    assert engine.tools == plugin.tools
    assert engine.top_k == 3
    assert engine.max_tool_rounds == 4
