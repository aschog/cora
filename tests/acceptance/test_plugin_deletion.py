"""The outer test for deleting a plugin: its entry, the documents of the field it
brought, and the conversation pinned to that field, all gone on one call from the page.
"""

import pathlib

from starlette.testclient import TestClient

from app_builder import assembled
from cora.adapters.file_output import FileOutput
from cora.app.assembly import LiveApp
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from fakes import (
    FakeConversations,
    FakeDocuments,
    FakeMemory,
    FakeRetriever,
    ScriptedChatModel,
)

DROPPED = """\
from cora.ports.host import Host


def extend(cora: Host) -> None:
    cora.register_instructions("Answer about birds.", scope="birds")
"""

THREAD = "watching"
QUESTION = "What did I see at dawn?"


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
    memory = FakeMemory(("You watch waders at dawn.",))
    output = FileOutput.at(str(tmp_path / "cora-output"))
    kept = pathlib.Path(output.write("dawn-list.md", "Twelve waders."))
    holder = LiveApp(
        named=(),
        folder=folder,
        compose=lambda loaded: assembled(
            plugins=loaded,
            chat_model=model,
            retriever=retriever,
            documents=documents,
            conversations=conversations,
            memory=memory,
            output=output,
            plugins_folder=folder,
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
    assert [each["text"] for each in reader.get("/api/memory").json()] == [
        "You watch waders at dawn."
    ], "what cora remembers is about the user, and outlives every field"
    assert kept.exists(), "what an approved effect wrote is the user's, not cora's"
