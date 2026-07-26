import pytest
from streamlit.testing.v1 import AppTest

from cora.app.assembly import App, assemble
from cora.core.ports.chat_model import ModelReply
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin


def _fake_app(answer: str = "Protein supports muscle growth [1].") -> App:
    return assemble(
        chat_model=ScriptedChatModel([ModelReply(text=answer)]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        plugin=make_plugin(),
    )


def _page(app) -> None:
    from cora.app.ui.chat import render

    render(app)


def _visible_text(at: AppTest) -> str:
    return "\n".join(md.value for md in at.markdown)


@pytest.mark.integration
def test_upload_then_ask_shows_answer_with_sources() -> None:
    at = AppTest.from_function(_page, args=(_fake_app(),))
    at.run()
    assert not at.exception

    at.file_uploader[0].set_value(("note.md", b"protein facts", "text/markdown"))
    at.run()
    assert not at.exception
    assert "note.md" in _visible_text(at)

    at.chat_input[0].set_value("What about protein?").run()
    assert not at.exception
    assert "Protein supports muscle growth [1]." in _visible_text(at)
    assert "[1] note.md" in _visible_text(at)
