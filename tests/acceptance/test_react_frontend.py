import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import App
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, FakeMemory, ScriptedChatModel
from sse import frames

DOCUMENT = "protein.md"
PASSAGE = "aim for 1.6 g of protein per kg of bodyweight"
SEED = f"# Protein\n\nFor strength training, {PASSAGE}.\n".encode()
QUESTION = "How much protein should I eat?"
ANSWER = "Your notes say 1.6 g per kg [1]."
THREAD = "the-only-conversation"


def _app() -> App:
    return assembled(
        chat_model=ScriptedChatModel(
            [
                ModelReply(
                    tool_calls=(
                        ToolCall(
                            name=SEARCH_TOOL_NAME,
                            arguments={"query": "protein"},
                            call_id="call-1",
                        ),
                    )
                ),
                ModelReply(text=ANSWER),
            ]
        ),
        memory=FakeMemory(),
        conversations=FakeConversations(),
    )


@pytest.mark.integration
def test_the_page_uploads_asks_reads_the_passage_and_comes_back_to_it() -> None:
    """The whole slice over the HTTP surface the page reads: a document arrives, a
    question is answered against it with its steps on the wire as they are taken, the
    citation opens onto the text its offsets were measured in, and the conversation is
    there to reopen afterwards."""
    with TestClient(api(_app(), plugins=("cora.plugins.fitness",))) as page:
        added = page.post(
            "/api/documents", files={"file": (DOCUMENT, SEED, "text/markdown")}
        )
        assert added.json()["chunks"] >= 1
        assert page.get("/api/documents").json() == [DOCUMENT]
        assert page.get("/api/plugins").json() == ["cora.plugins.fitness"]

        streamed = frames(
            page.post("/api/ask", json={"question": QUESTION, "thread_id": THREAD}).text
        )

        kinds = [name for name, _ in streamed]
        assert kinds[-1] == "turn" and kinds[:-1] == ["step"] * (len(kinds) - 1)
        turn = streamed[-1][1]
        assert turn["answer"] == ANSWER
        [citation] = turn["citations"]
        assert citation["document"] == DOCUMENT

        kept = page.get(f"/api/uploads/{citation['upload']}").json()["text"]
        assert PASSAGE in kept[citation["start"] : citation["end"]]

        [session] = page.get("/api/sessions").json()
        assert session["opened_with"] == QUESTION
        [reopened] = page.get(f"/api/sessions/{session['thread_id']}").json()
        assert reopened["question"] == QUESTION
        assert reopened["result"]["answer"] == ANSWER
