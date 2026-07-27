from dataclasses import dataclass, replace

import pytest
from streamlit.testing.v1 import AppTest

from cora.app.assembly import App, assemble
from cora.core.errors import (
    ConfigurationError,
    EmptyDocumentError,
    InputRejectedError,
    LlmError,
    PluginLoadError,
)
from cora.core.ports.chat_model import ChatModel, ModelReply
from cora.core.ports.plugin import Plugin, ToolCall
from cora.core.services.knowledge_base import KnowledgeBase
from fakes import (
    FailingChatModel,
    FakeEmbedder,
    FakeRetriever,
    ScriptedChatModel,
    add_tool,
)
from fixture_plugins import make_plugin


def _app(chat_model: ChatModel, plugin: Plugin | None = None) -> App:
    return assemble(
        chat_model=chat_model,
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        plugin=plugin or make_plugin(),
    )


class _CountingKnowledgeBase(KnowledgeBase):
    def __init__(self, inner: KnowledgeBase) -> None:
        super().__init__(embedder=inner.embedder, retriever=inner.retriever)
        self.ingests = 0

    def add_file(self, data: bytes, filename: str) -> int:
        self.ingests += 1
        return super().add_file(data, filename)


def _counting_app() -> tuple[App, _CountingKnowledgeBase]:
    app = _app(ScriptedChatModel([]))
    counting = _CountingKnowledgeBase(app.knowledge_base)
    return replace(app, knowledge_base=counting), counting


def _page(app) -> None:
    from cora.app.ui.chat import render

    render(app)


def _main_page(app_factory) -> None:
    from cora.app.ui.chat import main

    main(app_factory)


def _run_main(app_factory) -> AppTest:
    at = AppTest.from_function(_main_page, args=(app_factory,))
    at.run()
    return at


def _run_page(app: App) -> AppTest:
    at = AppTest.from_function(_page, args=(app,))
    at.run()
    return at


def _visible_text(at: AppTest) -> str:
    return "\n".join(md.value for md in at.markdown)


@pytest.mark.integration
def test_failed_turn_keeps_its_reason_across_a_rerun() -> None:
    at = _run_page(_app(FailingChatModel(LlmError())))

    at.chat_input[0].set_value("Hello?").run()
    at.run()

    assert not at.exception
    assert "Hello?" in _visible_text(at)
    assert [e.value for e in at.error] == [LlmError().user_message]
    assert at.chat_input


@dataclass(frozen=True)
class _RejectRule:
    phrase: str
    message: str

    def apply(self, user_input: str) -> None:
        if self.phrase in user_input:
            raise InputRejectedError(self.message)


@pytest.mark.integration
def test_thread_grows_past_a_failed_turn() -> None:
    refusal = "I can't advise on medication."
    answer = "BMI is weight over height squared."
    plugin = make_plugin(validation_rules=(_RejectRule("insulin", refusal),))
    at = _run_page(_app(ScriptedChatModel([ModelReply(text=answer)]), plugin=plugin))

    at.chat_input[0].set_value("Should I take insulin?").run()
    at.chat_input[0].set_value("What is BMI?").run()

    assert not at.exception
    text = _visible_text(at)
    assert "Should I take insulin?" in text
    assert "What is BMI?" in text
    assert answer in text
    assert [e.value for e in at.error] == [refusal]


@pytest.mark.integration
def test_upload_failure_shows_friendly_error_and_keeps_the_chat() -> None:
    at = _run_page(_app(ScriptedChatModel([])))

    at.file_uploader[0].set_value(("empty.txt", b"", "text/plain"))
    at.run()

    assert not at.exception
    expected = EmptyDocumentError("empty.txt").user_message
    assert [e.value for e in at.error] == [expected]
    assert at.chat_input


@pytest.mark.integration
def test_upload_error_clears_on_the_next_rerun_without_re_ingesting() -> None:
    app, knowledge_base = _counting_app()
    at = _run_page(app)

    at.file_uploader[0].set_value(("empty.txt", b"", "text/plain"))
    at.run()
    assert [e.value for e in at.error] == [EmptyDocumentError("empty.txt").user_message]

    at.run()

    assert not at.exception
    assert not at.error
    assert knowledge_base.ingests == 1


@pytest.mark.integration
def test_main_renders_the_page_from_the_factory() -> None:
    at = _run_main(lambda: _app(ScriptedChatModel([ModelReply(text="hi")])))

    assert not at.exception
    assert at.chat_input


@pytest.mark.integration
def test_main_without_config_shows_friendly_error_and_no_chat() -> None:
    def broken_factory() -> App:
        raise ConfigurationError("OPENROUTER_API_KEY is not set.")

    at = _run_main(broken_factory)

    assert not at.exception
    assert [e.value for e in at.error] == ["OPENROUTER_API_KEY is not set."]
    assert not at.chat_input


@pytest.mark.integration
def test_main_shows_friendly_error_for_any_startup_core_error() -> None:
    def broken_factory() -> App:
        raise PluginLoadError("cora.plugins.nutriton", "module not found")

    at = _run_main(broken_factory)

    assert not at.exception
    expected = PluginLoadError("cora.plugins.nutriton", "module not found")
    assert [e.value for e in at.error] == [expected.user_message]
    assert not at.chat_input


@pytest.mark.integration
def test_tool_results_are_shown_with_the_answer() -> None:
    call = ToolCall(name="add", arguments={"a": 17, "b": 25}, call_id="c1")
    scripted = ScriptedChatModel(
        [ModelReply(tool_calls=(call,)), ModelReply(text="Sum computed.")]
    )
    at = _run_page(_app(scripted, plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("17 + 25?").run()

    assert not at.exception
    assert "Sum computed." in _visible_text(at)
    assert "42" in _visible_text(at)


@pytest.mark.integration
def test_upload_then_ask_shows_answer_with_sources() -> None:
    answer = "Protein supports muscle growth [1]."
    at = _run_page(_app(ScriptedChatModel([ModelReply(text=answer)])))
    assert not at.exception

    at.file_uploader[0].set_value(("note.md", b"protein facts", "text/markdown"))
    at.run()
    assert not at.exception
    assert "note.md" in _visible_text(at)

    at.chat_input[0].set_value("What about protein?").run()
    assert not at.exception
    assert answer in _visible_text(at)
    assert "[1] note.md" in _visible_text(at)
