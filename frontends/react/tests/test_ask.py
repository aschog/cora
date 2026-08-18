import json

from starlette.testclient import TestClient

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.domain.errors import LlmError
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import Message, ModelReply
from cora.ports.plugin import Tool, ToolCall
from fakes import FailingChatModel, ScriptedChatModel

NOTES = b"Squats stall on sleep, not on volume. The block holds intensity."
SEARCH = ToolCall(name=SEARCH_TOOL_NAME, arguments={"query": "squats"}, call_id="c1")


def searching(answer: str = "Sleep, not volume [1].") -> ScriptedChatModel:
    return ScriptedChatModel(
        [ModelReply(tool_calls=(SEARCH,)), ModelReply(text=answer)]
    )


class BreaksAfterSearching:
    """A model that reaches the store and then cannot be reached itself: the shape of a
    turn that fails with steps already on the page."""

    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.completions += 1
        if self.completions == 1:
            return ModelReply(tool_calls=(SEARCH,))
        raise LlmError()


def asking(app: App, question: str = "Why?", thread: str = "t1") -> list[tuple]:
    """The stream, read as the (event, data) pairs it carried."""
    with TestClient(api(app)) as reader:
        streamed = reader.post(
            "/api/ask", json={"question": question, "thread_id": thread}
        )
    assert streamed.status_code == 200
    return [_parsed(frame) for frame in streamed.text.split("\n\n") if frame.strip()]


def _parsed(frame: str) -> tuple[str, dict]:
    name = data = ""
    for line in frame.splitlines():
        field, _, value = line.partition(": ")
        if field == "event":
            name = value
        elif field == "data":
            data = value
    return name, json.loads(data)


def test_the_steps_arrive_as_they_are_taken_and_the_answer_last() -> None:
    app = indexed(assembled(chat_model=searching()), ("notes.md", NOTES))

    streamed = asking(app)

    assert [name for name, _ in streamed] == ["step", "step", "step", "turn"]
    _, turn = streamed[-1]
    assert turn["answer"] == "Sleep, not volume [1]."
    assert [citation["document"] for citation in turn["citations"]] == ["notes.md"]
    assert [step["summary"] for step in turn["trace"]] == [
        step["summary"] for _, step in streamed[:-1]
    ]


def test_the_turn_is_the_last_thing_on_the_wire() -> None:
    """A client that stops reading at the turn has the whole answer."""
    app = indexed(assembled(chat_model=searching()), ("notes.md", NOTES))

    names = [name for name, _ in asking(app)]

    assert names[-1] == "turn"
    assert "turn" not in names[:-1]


def test_the_thread_the_client_names_is_the_thread_the_agent_answers_on() -> None:
    from fakes import FakeConversations

    conversations = FakeConversations()
    app = indexed(
        assembled(chat_model=searching(), conversations=conversations),
        ("notes.md", NOTES),
    )

    asking(app, question="Why the stall?", thread="continued")

    assert [session.thread_id for session in conversations.sessions()] == ["continued"]


def test_a_turn_that_fails_reports_after_the_steps_it_already_took() -> None:
    app = indexed(assembled(chat_model=BreaksAfterSearching()), ("notes.md", NOTES))

    streamed = asking(app)

    assert [name for name, _ in streamed] == ["step", "step", "error"]
    assert streamed[-1][1]["error"] == LlmError().user_message


def test_a_turn_that_fails_before_any_step_still_closes_the_stream() -> None:
    """A page waiting on an open connection is a page that never says what went
    wrong."""
    app = assembled(chat_model=FailingChatModel(LlmError()))

    streamed = asking(app)

    assert [name for name, _ in streamed] == ["error"]
