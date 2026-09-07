"""The outer test for deleting a conversation, over the surface the page reads."""

import pathlib
from functools import partial

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.adapters.langgraph_runner import langgraph_for
from cora.adapters.sqlite_conversations import SqliteConversations
from cora.app.assembly import App
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from fakes import ScriptedChatModel
from fixture_plugins import make_plugin

FITNESS = "fitness"
KEPT, DELETED = "t-kept", "t-deleted"
FIRST = "How much protein should I eat?"
SECOND = "And creatine?"
ANSWER = "Your notes say 1.6 g per kg."


def _app(path: pathlib.Path) -> App:
    """One file for both halves of a conversation, which is how a deployment keeps
    them: the turns a reader comes back to, and the thread the model answered on."""
    return assembled(
        chat_model=ScriptedChatModel([ModelReply(text=ANSWER)] * 2),
        conversations=SqliteConversations.at(str(path)),
        graph=partial(langgraph_for, checkpoints_at=str(path)),
        plugins=(make_plugin(name="coaching", scope=FITNESS),),
        scopes=(FITNESS,),
    )


def _listed(page: TestClient) -> list[str]:
    return [session["thread_id"] for session in page.get("/api/sessions").json()]


@pytest.mark.integration
def test_a_conversation_i_delete_is_gone_from_both_stores(
    tmp_path: pathlib.Path,
) -> None:
    served = api(_app(tmp_path / "conversations.sqlite"))
    with TestClient(served) as page:
        for thread, question in ((KEPT, FIRST), (DELETED, SECOND)):
            asked = {"question": question, "thread_id": thread, "pin": FITNESS}
            assert page.post("/api/ask", json=asked).status_code == 200
        assert _listed(page) == [DELETED, KEPT]

        assert page.delete(f"/api/sessions/{DELETED}").status_code == 204

        assert _listed(page) == [KEPT]
        assert page.get(f"/api/sessions/{DELETED}").json() == []
        assert page.get(f"/api/sessions/{DELETED}/scope").json() == {"pin": None}
