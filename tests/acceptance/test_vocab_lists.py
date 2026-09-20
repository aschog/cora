"""The outer test for the story: the vocab field brings a page, a list the page saved
lands in that field as a document, and cora answers about a word from there."""

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.engine.plugin_registry import load_plugin
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, ScriptedChatModel
from sse import frames

VOCAB = "vocab"
LIST = "lietuviu-einheit-3.md"
# What the page writes once the reader has corrected the reading: the heading names the
# language, and the table is German beside the language being learnt.
WORDS = (
    "# Lietuvių — Einheit 3\n\n"
    "| Deutsch | Lietuvių |\n| --- | --- |\n| Hilfe | pagalba |\n"
)
QUESTION = "Was heißt Hilfe auf Litauisch?"
ANSWER = "pagalba [1]."


@pytest.mark.xfail(strict=True, reason="the vocab plugin is what this change brings")
def test_the_vocab_page_is_served_and_what_it_saved_is_answered_from() -> None:
    app = assembled(
        plugins=(load_plugin("cora.plugins.vocab"),),
        chat_model=ScriptedChatModel(
            [
                ModelReply(
                    text="",
                    tool_calls=(
                        ToolCall(
                            name=SEARCH_TOOL_NAME,
                            arguments={"query": "Hilfe"},
                            call_id="call-1",
                        ),
                    ),
                ),
                ModelReply(text=ANSWER),
            ]
        ),
        conversations=FakeConversations(),
    )

    with TestClient(api(app)) as reader:
        where = reader.get("/api/scopes").json()["pages"][VOCAB]
        served = reader.get(where)
        assert served.status_code == 200
        assert "<!doctype html" in served.text.lower()
        # The page is what writes a list: it reads a screenshot where it was dropped,
        # and posts what the reader corrected to cora.
        assert "tesseract" in served.text.lower()
        assert "/api/documents" in served.text

        # What the page posts when the reader saves, and how it posts it.
        added = reader.post(
            "/api/documents",
            files={"file": (LIST, WORDS.encode(), "text/markdown")},
            data={"scope": VOCAB},
        )
        assert added.json()["scope"] == VOCAB
        assert reader.get(f"/api/documents?scope={VOCAB}").json() == [LIST]

        streamed = frames(
            reader.post(
                "/api/ask",
                json={"question": QUESTION, "thread_id": "t1", "pin": VOCAB},
            ).text
        )

    turn = streamed[-1][1]
    assert turn["answer"] == ANSWER
    [citation] = turn["citations"]
    assert citation["document"] == LIST
