"""The outer test for deleting a plugin: its entry, the documents of the field it
brought, and the conversation pinned to that field, all gone on one call from the page.
"""

import pathlib

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import LiveApp
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from fakes import FakeConversations, FakeDocuments, FakeRetriever, ScriptedChatModel

DROPPED = """\
from cora.ports.host import Host


def extend(cora: Host) -> None:
    cora.register_instructions("Answer about birds.", scope="birds")
"""

THREAD = "watching"
QUESTION = "What did I see at dawn?"


@pytest.mark.xfail(strict=True, reason="the delete route is not written yet")
def test_deleting_a_plugin_takes_its_documents_and_its_conversation(
    tmp_path: pathlib.Path,
) -> None:
    folder = tmp_path / "plugins"
    folder.mkdir()
    dropped = folder / "field_notes.py"
    dropped.write_text(DROPPED)
    conversations, retriever, documents = (
        FakeConversations(),
        FakeRetriever(),
        FakeDocuments(),
    )
    model = ScriptedChatModel([ModelReply(text="Twelve waders.")])
    holder = LiveApp(
        named=(),
        folder=folder,
        compose=lambda loaded: assembled(
            plugins=loaded,
            chat_model=model,
            retriever=retriever,
            documents=documents,
            conversations=conversations,
        ),
    )
    reader = TestClient(api(holder))
    reader.post(
        "/api/documents",
        files={"file": ("sightings.md", b"Twelve waders at dawn.", "text/markdown")},
        data={"scope": "birds"},
    )
    with reader.stream(
        "POST",
        "/api/ask",
        json={"question": QUESTION, "thread_id": THREAD, "pin": "birds"},
    ) as answering:
        answering.read()

    assert reader.get("/api/documents?scope=birds").json() == ["sightings.md"]
    assert [each["thread_id"] for each in reader.get("/api/sessions").json()] == [
        THREAD
    ]

    gone = reader.delete("/api/plugins/field_notes")

    assert gone.status_code == 204
    assert not dropped.exists()
    assert reader.get("/api/scopes").json()["available"] == []
    assert reader.get("/api/documents?scope=birds").status_code == 400
    assert reader.get("/api/sessions").json() == []
