"""The outer test for story 3, over the surface the page reads."""

import pathlib

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.adapters.sqlite_store_memory import SqliteStoreMemory
from cora.app.assembly import App
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, ScriptedChatModel

FACT = "The user is vegetarian."
SHARED = "I'm vegetarian — keep that in mind."
ACKNOWLEDGED = "Noted, I'll remember that."
LATER = "What should I eat after training?"
ADVICE = "Lentils and tofu rebuild protein after a session."


def _remembering() -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(name=REMEMBER_TOOL_NAME, arguments={"fact": FACT}, call_id="m1"),
        )
    )


def _app(path: pathlib.Path, chat_model: ChatModel) -> App:
    """A store that outlives the process, which is the whole subject: the fact has to
    survive an app being thrown away, not a variable being reassigned."""
    return assembled(
        chat_model=chat_model,
        memory=SqliteStoreMemory.at(str(path)),
        conversations=FakeConversations(),
    )


def _asked(app: App, question: str) -> TestClient:
    with TestClient(api(app)) as page:
        page.post("/api/ask", json={"question": question, "thread_id": "t1"})
        return page


def _remembered(page: TestClient) -> list[str]:
    return [fact["text"] for fact in page.get("/api/memory").json()]


@pytest.mark.integration
def test_a_fact_shared_last_session_briefs_the_model_the_next(
    tmp_path: pathlib.Path,
) -> None:
    """The criterion end to end: one session tells it something, a fresh session over
    the same memory file answers with it in hand and lists what it is holding."""
    path = tmp_path / "memory.sqlite"
    told = ScriptedChatModel([_remembering(), ModelReply(text=ACKNOWLEDGED)])
    _asked(_app(path, told), SHARED)

    asked = ScriptedChatModel([ModelReply(text=ADVICE)])
    with TestClient(api(_app(path, asked))) as page:
        answered = page.post("/api/ask", json={"question": LATER, "thread_id": "t2"})

        assert answered.status_code == 200
        assert ADVICE in answered.text
        assert asked.last_messages is not None
        assert FACT in asked.last_messages[0].content
        assert FACT in _remembered(page)


@pytest.mark.integration
def test_clearing_the_panel_empties_the_store_and_the_next_brief(
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "memory.sqlite"
    told = ScriptedChatModel([_remembering(), ModelReply(text=ACKNOWLEDGED)])
    _asked(_app(path, told), SHARED)

    asked = ScriptedChatModel([ModelReply(text=ADVICE), ModelReply(text=ADVICE)])
    with TestClient(api(_app(path, asked))) as page:
        page.post("/api/ask", json={"question": LATER, "thread_id": "t2"})
        assert asked.last_messages is not None
        assert FACT in asked.last_messages[0].content

        assert page.delete("/api/memory").status_code == 204
        page.post("/api/ask", json={"question": LATER, "thread_id": "t3"})

        assert _remembered(page) == []
        assert FACT not in asked.last_messages[0].content
