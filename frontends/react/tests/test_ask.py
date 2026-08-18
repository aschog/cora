import json
import logging
import threading

import anyio
import pytest
from starlette.testclient import TestClient

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.domain.errors import LlmError
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import Message, ModelReply
from cora.ports.plugin import Tool, ToolCall
from fakes import FailingChatModel, ScriptedChatModel
from sse import frames

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


def asking(
    app: App, question: str = "Why?", thread: str = "t1"
) -> list[tuple[str, dict]]:
    """The stream, read as the (event, data) pairs it carried."""
    with TestClient(api(app)) as reader:
        streamed = reader.post(
            "/api/ask", json={"question": question, "thread_id": thread}
        )
    assert streamed.status_code == 200
    assert streamed.headers["content-type"].startswith("text/event-stream")
    assert streamed.headers["cache-control"] == "no-cache"
    assert streamed.headers["x-accel-buffering"] == "no", (
        "a proxy that buffers the response delivers every step at the end, which is "
        "the shape this endpoint exists not to have"
    )
    return frames(streamed.text)


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


class BreaksInAWayNobodyModelled:
    """A tool or an adapter raising something that is not a `CoreError` — a plugin
    handed a payload it did not expect, say."""

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        raise KeyError("range")


def test_what_the_reader_is_spared_is_written_to_the_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The screen gets a sentence and the operator gets the stack. Keeping the
    exception off the page is only defensible while the log still has it — otherwise
    the failure exists nowhere."""
    with caplog.at_level(logging.ERROR, logger="cora.frontends.react.api"):
        asking(assembled(chat_model=BreaksInAWayNobodyModelled()))

    [logged] = caplog.records
    assert logged.exc_info is not None
    assert "KeyError" in caplog.text


def test_a_failure_nobody_modelled_still_says_the_turn_went_wrong() -> None:
    """Ending the stream without an `error` reads to the page as a cut connection, so a
    reader retries a question that will fail the same way. The message is generic: an
    exception's text is for the log, not for the screen."""
    streamed = asking(assembled(chat_model=BreaksInAWayNobodyModelled()))

    assert [name for name, _ in streamed] == ["error"]
    said = streamed[0][1]["error"]
    assert "range" not in said and "KeyError" not in said
    assert said


@pytest.mark.parametrize("body", ["not json at all", "[]", '"just a string"'])
def test_a_body_that_is_not_a_question_is_refused_rather_than_a_crash(
    body: str,
) -> None:
    """The error contract holds at the door too: `_ingest` already answers a missing
    file with a message and a 400, and asking is no different."""
    with TestClient(api(assembled())) as reader:
        refused = reader.post(
            "/api/ask", content=body, headers={"Content-Type": "application/json"}
        )

    assert refused.status_code == 400
    assert refused.json()["error"]


class WaitsToAnswer:
    """Reaches the store, then holds the turn open until it is let go. What a real model
    does for thirty seconds, made exact: while it waits, the steps already taken either
    are on the wire or are not."""

    def __init__(self, entered: threading.Event, released: threading.Event) -> None:
        self.entered = entered
        self.released = released
        self.completions = 0

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        self.completions += 1
        if self.completions == 1:
            return ModelReply(tool_calls=(SEARCH,))
        self.entered.set()
        self.released.wait(timeout=WAITS_FOREVER)
        return ModelReply(text="Sleep, not volume [1].")


async def _asked_mid_turn(
    served: object, entered: threading.Event, released: threading.Event
) -> tuple[list[str], bool | None]:
    """Drive the ASGI app itself, because `TestClient` buffers a response before it
    hands it over — the one thing this test is about is invisible through it. Each
    `http.response.body` message is one chunk as the server sent it; the first is
    checked against the turn still being in flight, and letting the model go is what
    that check releases."""
    chunks: list[str] = []
    mid_turn: bool | None = None

    asked = json.dumps({"question": "Why?", "thread_id": "t1"}).encode()
    delivered = False

    async def receive() -> dict:
        """The body once, and then nothing — a reader who has not disconnected simply
        never speaks again. Answering a second time feeds the response's own
        disconnect watcher in a loop, which starves the event loop it runs on."""
        nonlocal delivered
        if delivered:
            await anyio.sleep_forever()
        delivered = True
        return {"type": "http.request", "body": asked, "more_body": False}

    async def send(message: dict) -> None:
        nonlocal mid_turn
        if message["type"] != "http.response.body" or not message.get("body"):
            return
        chunks.append(message["body"].decode())
        if mid_turn is not None:
            return
        # Wait for the model to be inside `complete` rather than asking whether it has
        # got there yet: a chunk can reach the loop before the worker is scheduled that
        # far, and `is_set()` here would read that ordering as a failure. Waiting makes
        # the claim exact — this chunk was on the wire while the turn was unfinished,
        # because the only thing that ends the turn is the release below.
        mid_turn = entered.wait(HOLDS_THE_TURN)
        released.set()

    await served(SCOPE, receive, send)  # ty: ignore[call-non-callable]
    return chunks, mid_turn


SCOPE = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.3"},
    "http_version": "1.1",
    "method": "POST",
    "path": "/api/ask",
    "raw_path": b"/api/ask",
    "root_path": "",
    "scheme": "http",
    "query_string": b"",
    "headers": [(b"content-type", b"application/json")],
    "client": ("test", 1),
    "server": ("test", 80),
}


def test_a_step_reaches_the_page_while_the_turn_is_still_running() -> None:
    """The one assertion that tells a stream from a response: with the model still
    inside `complete`, a step the agent has already taken is already on the wire. Batch
    the events and send them at the end and nothing arrives until the model returns —
    which cannot happen until the first chunk releases it, so this goes red rather than
    quietly measuring nothing."""
    entered, released = threading.Event(), threading.Event()
    app = indexed(
        assembled(chat_model=WaitsToAnswer(entered, released)), ("notes.md", NOTES)
    )

    try:
        chunks, mid_turn = anyio.run(
            _within, HOLDS_THE_TURN, _asked_mid_turn, api(app), entered, released
        )
    finally:
        released.set()

    assert mid_turn, "nothing reached the page while the answer was still being written"
    streamed = frames("".join(chunks))
    assert streamed[0][0] == "step"
    assert [name for name, _ in streamed][-1] == "turn"


HOLDS_THE_TURN = 3
"""How long the run is given. Long enough that a slow machine still streams, and well
inside the model's own patience below — a turn that batches its events must fail on
*this* deadline, not be rescued by the model giving up and finishing anyway."""

WAITS_FOREVER = 60
"""The model waits to be released rather than to be timed out; the number is only a
backstop so a test that never releases cannot hang the suite."""


async def _within(seconds: float, work, *args):
    with anyio.fail_after(seconds):
        return await work(*args)
