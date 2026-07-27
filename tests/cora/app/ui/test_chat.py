from dataclasses import dataclass

import pytest
from streamlit.testing.v1 import AppTest

from cora.app.assembly import App, assemble
from cora.core.chunk import Chunk
from cora.core.errors import (
    ConfigurationError,
    EmptyDocumentError,
    InputRejectedError,
    LlmError,
    PluginLoadError,
    RetrievalError,
)
from cora.core.ports.chat_model import ChatModel, ModelReply
from cora.core.ports.plugin import Plugin, ToolCall
from cora.core.ports.retrieval import Retriever
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


class _CountingRetriever(FakeRetriever):
    """Counts ingest attempts: ``add_file`` asks ``contains`` before any work."""

    def __init__(self) -> None:
        super().__init__()
        self.ingest_attempts = 0

    def contains(self, file_hash: str) -> bool:
        self.ingest_attempts += 1
        return super().contains(file_hash)


class _FlakyRetriever(FakeRetriever):
    def __init__(self) -> None:
        super().__init__()
        self.failures = 0

    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None:
        if self.failures:
            self.failures -= 1
            raise RetrievalError
        super().add(chunks, vectors, file_hash)


def _app_on(retriever: Retriever, plugin: Plugin | None = None) -> App:
    return assemble(
        chat_model=ScriptedChatModel([]),
        embedder=FakeEmbedder(),
        retriever=retriever,
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


def _sidebar_sources(at: AppTest) -> list[str]:
    return [md.value for md in at.sidebar.markdown]


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
def test_a_failure_carrying_no_message_still_renders_as_an_error() -> None:
    plugin = make_plugin(validation_rules=(_RejectRule("insulin", ""),))
    at = _run_page(_app(ScriptedChatModel([]), plugin=plugin))

    at.chat_input[0].set_value("Should I take insulin?").run()

    assert not at.exception
    assert len(at.error) == 1


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
def test_successful_upload_confirms_with_its_chunk_count() -> None:
    at = _run_page(_app(ScriptedChatModel([])))

    at.file_uploader[0].set_value(("note.md", b"protein facts", "text/markdown"))
    at.run()

    assert not at.exception
    [confirmation] = at.success
    assert "note.md" in confirmation.value
    assert "1 chunk" in confirmation.value


@pytest.mark.integration
def test_uploading_content_already_indexed_reports_a_duplicate() -> None:
    plugin = make_plugin(seed_docs=(("seed.md", b"protein facts"),))
    at = _run_page(_app(ScriptedChatModel([]), plugin=plugin))

    at.file_uploader[0].set_value(("copy.md", b"protein facts", "text/markdown"))
    at.run()

    assert not at.exception
    assert not at.success
    [notice] = at.info
    assert "copy.md" in notice.value


@pytest.mark.integration
def test_a_new_selection_of_known_bytes_reports_the_duplicate() -> None:
    at = _run_page(_app(ScriptedChatModel([])))
    content = b"protein facts"

    at.file_uploader[0].set_value(("a.md", content, "text/markdown"))
    at.run()
    at.file_uploader[0].set_value(("b.md", content, "text/markdown"))
    at.run()

    assert not at.exception
    assert not at.success
    [notice] = at.info
    assert "b.md" in notice.value


@pytest.mark.integration
def test_a_transient_ingest_failure_is_retried_on_the_next_rerun() -> None:
    retriever = _FlakyRetriever()
    at = _run_page(_app_on(retriever))
    retriever.failures = 1

    at.file_uploader[0].set_value(("note.md", b"protein facts", "text/markdown"))
    at.run()
    assert [e.value for e in at.error] == [RetrievalError().user_message]

    at.run()

    assert not at.exception
    assert not at.error
    [confirmation] = at.success
    assert "note.md" in confirmation.value


@pytest.mark.integration
def test_upload_error_clears_on_the_next_rerun_without_re_ingesting() -> None:
    retriever = _CountingRetriever()
    plugin = make_plugin(seed_docs=(("seed.md", b"protein facts"),))
    at = _run_page(_app_on(retriever, plugin))
    retriever.ingest_attempts = 0

    at.file_uploader[0].set_value(("empty.txt", b"", "text/plain"))
    at.run()
    assert [e.value for e in at.error] == [EmptyDocumentError("empty.txt").user_message]

    at.run()

    assert not at.exception
    assert not at.error
    assert retriever.ingest_attempts == 1
    assert _sidebar_sources(at) == ["seed.md"]


@pytest.mark.integration
def test_detaching_a_file_lets_the_same_bytes_be_selected_again() -> None:
    retriever = _CountingRetriever()
    at = _run_page(_app_on(retriever))
    upload = ("note.md", b"protein facts", "text/markdown")

    at.file_uploader[0].set_value(upload)
    at.run()
    at.file_uploader[0].clear()
    at.run()
    at.file_uploader[0].set_value(upload)
    at.run()

    assert not at.exception
    assert retriever.ingest_attempts == 2
    [notice] = at.info
    assert "already in your knowledge base" in notice.value


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
