import pytest
from streamlit.testing.v1 import AppTest

from cora.app.assembly import App, assemble
from cora.core.errors import (
    ConfigurationError,
    EmptyDocumentError,
    LlmError,
    PluginLoadError,
)
from cora.core.ports.chat_model import ChatModel, ModelReply
from cora.core.ports.plugin import Plugin, ToolCall
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
def test_engine_error_shows_friendly_message_and_keeps_the_thread() -> None:
    at = _run_page(_app(FailingChatModel(LlmError())))

    at.chat_input[0].set_value("Hello?").run()

    assert not at.exception
    assert [e.value for e in at.error] == [LlmError().user_message]
    assert "Hello?" in _visible_text(at)
    assert at.chat_input


@pytest.mark.integration
def test_failed_turn_keeps_its_reason_across_a_rerun() -> None:
    at = _run_page(_app(FailingChatModel(LlmError())))

    at.chat_input[0].set_value("Hello?").run()
    at.run()

    assert not at.exception
    assert "Hello?" in _visible_text(at)
    assert [e.value for e in at.error] == [LlmError().user_message]


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
