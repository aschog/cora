import datetime

from starlette.testclient import TestClient

from app_builder import assembled
from cora.engine.plugin_registry import load_plugin
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, ScriptedChatModel
from sse import frames

FITNESS = "fitness"
# What the trainer really writes, taken from the plan it ships: a fixture the page
# could not produce would prove retrieval against text nobody will ever have.
WORKOUT = "# One-arm kettlebell snatch 24 kg\n3 sets of 10\n"
QUESTION = "What did I snatch?"
ANSWER = "Three sets of ten at 24 kg [1]."


def test_the_trainer_is_served_and_what_it_finishes_is_answered_from() -> None:
    today = f"{datetime.date.today().isoformat()}.md"
    app = assembled(
        plugins=(load_plugin("cora.plugins.fitness"),),
        chat_model=ScriptedChatModel(
            [
                ModelReply(
                    text="",
                    tool_calls=(
                        ToolCall(
                            name=SEARCH_TOOL_NAME,
                            arguments={"query": "snatch"},
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
        where = reader.get("/api/scopes").json()["pages"][FITNESS]
        served = reader.get(where)
        assert served.status_code == 200
        assert "<!doctype html" in served.text.lower()

        # What the trainer posts when the reader finishes, and how it posts it.
        added = reader.post(
            "/api/documents",
            files={"file": (today, WORKOUT.encode(), "text/markdown")},
            data={"scope": FITNESS},
        )
        assert added.json()["scope"] == FITNESS
        assert reader.get(f"/api/documents?scope={FITNESS}").json() == [today]

        streamed = frames(
            reader.post(
                "/api/ask",
                json={"question": QUESTION, "thread_id": "t1", "pin": FITNESS},
            ).text
        )

    turn = streamed[-1][1]
    assert turn["answer"] == ANSWER
    [citation] = turn["citations"]
    assert citation["document"] == today
