import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import App
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, FakeMemory, ScriptedChatModel
from sse import frames

DOCUMENT = "protein.md"
PASSAGE = "aim for 1.6 g of protein per kg of bodyweight"
SEED = f"# Protein\n\nFor strength training, {PASSAGE}.\n".encode()
QUESTION = "How much protein should I eat?"
PREAMBLE = "Let me look at your notes. "
ANSWER = "Your notes say 1.6 g per kg [1]."
THREAD = "the-only-conversation"


def _app(chat_model: ChatModel | None = None) -> App:
    return assembled(
        chat_model=chat_model
        or ScriptedChatModel(
            [
                ModelReply(
                    text=PREAMBLE,
                    tool_calls=(
                        ToolCall(
                            name=SEARCH_TOOL_NAME,
                            arguments={"query": "protein"},
                            call_id="call-1",
                        ),
                    ),
                ),
                ModelReply(text=ANSWER),
            ]
        ),
        memory=FakeMemory(),
        conversations=FakeConversations(),
    )


@pytest.mark.integration
def test_the_page_uploads_asks_reads_the_passage_and_comes_back_to_it() -> None:
    with TestClient(api(_app())) as page:
        added = page.post(
            "/api/documents", files={"file": (DOCUMENT, SEED, "text/markdown")}
        )
        assert added.json()["chunks"] >= 1
        assert page.get("/api/documents").json() == [DOCUMENT]
        listed = page.get("/api/plugins").json()
        assert [each["name"] for each in listed] == ["valid"]

        streamed = frames(
            page.post("/api/ask", json={"question": QUESTION, "thread_id": THREAD}).text
        )

        kinds = [name for name, _ in streamed]
        assert kinds[-1] == "turn" and set(kinds[:-1]) <= {"step", "text", "aside"}
        turn = streamed[-1][1]
        assert turn["answer"] == ANSWER
        # The answer arrived in pieces before it arrived whole, and the two agree — the
        # page draws the pieces as they land and the turn's own text once it does. The
        # model wrote before it searched, so the pieces are the ones since the aside
        # said the round they belonged to was not the answer.
        after = streamed[kinds.index("aside") + 1 :]
        written = "".join(data["text"] for name, data in after if name == "text")
        assert written == turn["answer"]
        assert PREAMBLE in "".join(
            data["text"] for name, data in streamed if name == "text"
        )
        [citation] = turn["citations"]
        assert citation["document"] == DOCUMENT

        opened = f"/api/uploads/{citation['scope']}/{citation['upload']}"
        kept = page.get(opened).json()["text"]
        assert PASSAGE in kept[citation["start"] : citation["end"]]

        [session] = page.get("/api/conversations").json()
        assert session["opened_with"] == QUESTION
        [reopened] = page.get(f"/api/conversations/{session['thread_id']}").json()
        assert reopened["question"] == QUESTION
        assert reopened["result"]["answer"] == ANSWER
