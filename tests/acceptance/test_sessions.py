"""The outer test for deleting a conversation, over the surface the page reads."""

import pathlib
from functools import partial

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.adapters.langgraph_runner import langgraph_for
from cora.adapters.sqlite_conversations import SqliteConversations
from cora.adapters.sqlite_store_memory import SqliteStoreMemory
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
    return assembled(
        chat_model=ScriptedChatModel([ModelReply(text=ANSWER)] * 2),
        conversations=SqliteConversations.at(str(path)),
        memory=SqliteStoreMemory.at(str(path)),
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
    served = api(_app(tmp_path / "cora.sqlite"))
    with TestClient(served) as page:
        for thread, question in ((KEPT, FIRST), (DELETED, SECOND)):
            asked = {"question": question, "thread_id": thread, "pin": FITNESS}
            assert page.post("/api/ask", json=asked).status_code == 200
        assert _listed(page) == [DELETED, KEPT]

        assert page.delete(f"/api/sessions/{DELETED}").status_code == 204

        assert _listed(page) == [KEPT]
        assert page.get(f"/api/sessions/{DELETED}").json() == []
        assert page.get(f"/api/sessions/{DELETED}/scope").json() == {"pin": None}


@pytest.mark.integration
def test_a_thread_is_picked_up_out_of_the_file_by_a_second_composition(
    tmp_path: pathlib.Path,
) -> None:
    """A checkpoint is state the file holds, not the process: the pin a turn was
    answered under is read back by an app that never saw that turn."""
    store = tmp_path / "cora.sqlite"
    with TestClient(api(_app(store))) as page:
        asked = {"question": FIRST, "thread_id": KEPT, "pin": FITNESS}
        assert page.post("/api/ask", json=asked).status_code == 200

    with TestClient(api(_app(store))) as reopened:
        assert reopened.get(f"/api/sessions/{KEPT}/scope").json() == {"pin": FITNESS}
        assert _listed(reopened) == [KEPT]
