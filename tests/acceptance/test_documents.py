"""The outer tests for a field's own documents: what it answers from, and what it
stops answering from once a document is deleted.

Uploads go through the API because that is where an upload names its field. The turn
is asked of the agent directly, so the assertion is about what a pinned turn could
retrieve and cite rather than about the stream that carries it.
"""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.adapters.file_documents import FileDocuments
from cora.domain.chat_result import ChatResult
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, FakeEmbedder, ScriptedChatModel
from fixture_plugins import make_plugin

if TYPE_CHECKING:
    from cora.adapters.sqlite_vec_retriever import SqliteVecRetriever

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
    client = TestClient(api(app))
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


MAPLES = b"The maples turn in the second week of November."
NOTES = ModelReply(text="They say the maples turn in November [1].")


@pytest.mark.integration
def test_a_document_i_delete_is_searched_and_cited_no_more(
    tmp_path: Path,
    make_index: "Callable[[], SqliteVecRetriever]",
) -> None:
    """Over the real index and the real files, because both halves are the subject: a
    document gone from one of them is a document that is still half there."""
    files = tmp_path / "documents"
    app = assembled(
        chat_model=ScriptedChatModel([SEARCH, NOTES]),
        embedder=FakeEmbedder(),
        retriever=make_index(),
        documents=FileDocuments.at(str(files)),
        conversations=FakeConversations(),
        plugins=(
            make_plugin(
                name="trips", instructions="A companion.", tools=(), scope=TRAVEL
            ),
        ),
        scopes=(TRAVEL,),
    )
    client = TestClient(api(app))
    _upload(client, "kyoto.md", KYOTO, TRAVEL)
    _upload(client, "maples.md", MAPLES, TRAVEL)

    deleted = client.delete(f"/api/documents/{TRAVEL}/kyoto.md")

    assert deleted.status_code == 204
    assert client.get(f"/api/documents?scope={TRAVEL}").json() == ["maples.md"]

    answered: ChatResult = app.agent.answer(QUESTION, THREAD, pin=TRAVEL)
    assert {cited.document for cited in answered.citations} == {"maples.md"}

    left = [kept.name for kept in (files / TRAVEL).iterdir()]
    assert len(left) == 1, f"the deleted document's file is still there: {left}"
    assert left[0].startswith("maples-")
