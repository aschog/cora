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
LIST = "english-einheit-3.md"
# A list as the field holds one: the heading names the language, and the table is German
# beside the language being learnt.
WORDS = (
    "# English — Einheit 3\n\n| Deutsch | English |\n| --- | --- |\n| Hilfe | help |\n"
)
QUESTION = "Was heißt Hilfe auf Englisch?"
ANSWER = "help [1]."


def test_a_word_is_answered_from_the_list_it_was_uploaded_on() -> None:
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
        assert VOCAB in reader.get("/api/scopes").json()["available"]

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
