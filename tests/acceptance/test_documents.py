"""Story 8's outer test: a field answers from its own files, and nothing else's.

Uploads go through the API because that is where an upload names its field. The turn
is asked of the agent directly, so the assertion is about what a pinned turn could
retrieve and cite rather than about the stream that carries it.
"""

from starlette.testclient import TestClient

from app_builder import assembled
from cora.domain.chat_result import ChatResult
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, ScriptedChatModel
from fixture_plugins import make_plugin

FITNESS, TRAVEL = "fitness", "travel"
PLAN = b"The block holds intensity and drops volume in the fourth week."
KYOTO = b"The sleeper to Kyoto sells out a month before the maples turn."
QUESTION = "What do my notes say?"
THREAD = "t1"
SEARCH = ModelReply(
    tool_calls=(
        ToolCall(name=SEARCH_TOOL_NAME, arguments={"query": QUESTION}, call_id="c1"),
    )
)
ANSWER = ModelReply(text="They say the sleeper sells out early [1][2].")


def test_a_field_answers_from_its_own_files() -> None:
    app = assembled(
        chat_model=ScriptedChatModel([SEARCH, ANSWER]),
        conversations=FakeConversations(),
        plugins=(
            make_plugin(
                name="coaching", instructions="A coach.", tools=(), scope=FITNESS
            ),
            make_plugin(
                name="trips", instructions="A companion.", tools=(), scope=TRAVEL
            ),
        ),
        scopes=(FITNESS, TRAVEL),
    )
    client = TestClient(api(app, scopes=(FITNESS, TRAVEL)))
    _upload(client, "plan.md", PLAN, FITNESS)
    _upload(client, "kyoto.md", KYOTO, TRAVEL)

    result: ChatResult = app.agent.answer(QUESTION, THREAD, pin=TRAVEL)

    assert {cited.document for cited in result.citations} == {"kyoto.md"}
    assert client.get(f"/api/documents?scope={TRAVEL}").json() == ["kyoto.md"]
    [citation] = result.citations
    opened = client.get(f"/api/uploads/{TRAVEL}/{citation.upload}")
    assert opened.status_code == 200
    assert opened.json()["text"] == KYOTO.decode()


def _upload(client: TestClient, name: str, data: bytes, scope: str) -> None:
    added = client.post(
        "/api/documents",
        files={"file": (name, data, "text/markdown")},
        data={"scope": scope},
    )
    assert added.status_code == 200
