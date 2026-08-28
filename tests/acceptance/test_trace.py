"""What a turn did, read off the wire the page reads it from."""

import pytest
from starlette.testclient import TestClient

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, FakeMemory, ScriptedChatModel, add_tool
from fixture_plugins import make_plugin
from sse import frames

SEED_DOC = ("note.md", b"protein builds muscle")
QUESTION = "What do my notes say about protein, and what is 20 + 22?"
ANSWER = "Protein builds muscle [1], and 20 + 22 = 42."


def _call(name: str, call_id: str, **arguments: object) -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name=name, arguments=arguments, call_id=call_id),)
    )


def _app() -> App:
    return indexed(
        assembled(
            chat_model=ScriptedChatModel(
                [
                    _call(SEARCH_TOOL_NAME, "call-1", query="protein"),
                    _call("add", "call-2", a=20, b=22),
                    ModelReply(text=ANSWER),
                ]
            ),
            plugin=make_plugin(tools=(add_tool(),)),
            memory=FakeMemory(),
            conversations=FakeConversations(),
        ),
        SEED_DOC,
    )


@pytest.mark.integration
def test_the_trace_shows_each_step_with_its_tool_arguments_and_result() -> None:
    """One turn that searches, calculates and then answers, with every step it took on
    the wire — what it decided, the call it made with the arguments it made it with, and
    what came back."""
    with TestClient(api(_app())) as page:
        streamed = frames(
            page.post("/api/ask", json={"question": QUESTION, "thread_id": "t1"}).text
        )

    name, turn = streamed[-1]
    assert name == "turn", f"the turn did not finish: {streamed[-1]}"
    assert turn["answer"] == ANSWER
    said = "\n".join(f"{step['summary']}\n{step['detail']}" for step in turn["trace"])
    assert f"Decided to call {SEARCH_TOOL_NAME}" in said
    assert f'{SEARCH_TOOL_NAME}(query="protein")' in said
    assert "1 passage from note.md" in said
    assert "add(a=20, b=22)" in said
    assert "42" in said
    assert "Decided no tool was needed" in said
    assert "[1] note.md: protein builds muscle" in said, (
        "the passage the search returned is what the step's detail is for"
    )
