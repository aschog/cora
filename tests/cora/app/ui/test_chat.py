import pytest
from streamlit.testing.v1 import AppTest

from cora.app.assembly import App, assemble
from cora.core.errors import LlmError
from cora.core.ports.chat_model import ChatModel, ModelReply
from fakes import FailingChatModel, FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin


def _app(chat_model: ChatModel) -> App:
    return assemble(
        chat_model=chat_model,
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        plugin=make_plugin(),
    )


def _page(app) -> None:
    from cora.app.ui.chat import render

    render(app)


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
    assert at.chat_input[0] is not None


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
