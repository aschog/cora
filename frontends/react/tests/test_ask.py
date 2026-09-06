import json
import logging
import threading
from collections.abc import Iterator

import anyio
import pytest
from starlette.testclient import TestClient

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.domain.approval import TOOL
from cora.domain.errors import LlmError
from cora.engine.ask_tool import ASK_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.engine.validation import MAX_INPUT_CHARS
from cora.frontends.react.api import (
    MAX_ASK_BYTES,
    NOT_A_DECISION,
    NOT_A_QUESTION,
    NOT_FILLED_IN,
    NOT_THAT_CARD,
    REFUSED,
    TOO_LONG_TO_ASK,
    api,
)
from cora.ports.chat_model import Message, ModelReply, Piece, TextSink, unheard
from cora.ports.host import Extension, Host
from cora.ports.plugin import Tool, ToolCall
from fakes import FailingChatModel, FakeConversations, ScriptedChatModel
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
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
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

    assert [name for name, _ in streamed] == [
        "step",  # screen
        "step",  # route
        "step",  # the scope it settled on
        "step",  # focus
        "step",  # work
        "step",  # the round that searched
        "step",  # what the search found
        "text",
        "step",  # the round that answered
        "step",  # answer
        "turn",
    ]
    _, turn = streamed[-1]
    assert turn["answer"] == "Sleep, not volume [1]."
    assert [citation["document"] for citation in turn["citations"]] == ["notes.md"]
    assert [step["summary"] for step in turn["trace"]] == [
        step["summary"] for name, step in streamed[:-1] if name == "step"
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

    assert [name for name, _ in streamed] == [
        "step",  # screen
        "step",  # route
        "step",  # the scope it settled on
        "step",  # focus
        "step",  # work
        "step",  # the round that searched
        "step",  # what the search found
        "error",
    ]
    assert streamed[-1][1]["error"] == LlmError().user_message


def test_a_turn_that_fails_before_any_round_still_closes_the_stream() -> None:
    """A page waiting on an open connection is a page that never says what went
    wrong. The turn had walked as far as its first round, so the page holds those steps
    and the error after them."""
    app = assembled(chat_model=FailingChatModel(LlmError()))

    streamed = asking(app)

    assert [name for name, _ in streamed] == [
        "step",  # screen
        "step",  # route
        "step",  # the scope it settled on
        "step",  # focus
        "step",  # work
        "error",
    ]


class BreaksInAWayNobodyModelled:
    """A tool or an adapter raising something that is not a `CoreError` — a plugin
    handed a payload it did not expect, say."""

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
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

    assert [name for name, _ in streamed][-1] == "error"
    said = streamed[-1][1]["error"]
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
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
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


@pytest.mark.parametrize(
    "asked",
    [
        {"question": "  ", "thread_id": "t1"},
        {"thread_id": "t1"},
        {"question": "Why?"},
        {"question": "Why?", "thread_id": " "},
        {"question": 7, "thread_id": "t1"},
    ],
)
def test_a_body_missing_either_half_is_refused_rather_than_answered(
    asked: dict[str, object],
) -> None:
    """`NOT_A_QUESTION` names both halves — a question, and the thread it belongs to —
    and was only ever returned for a body that would not parse at all. A blank of either
    was answered instead: a worker thread, a graph run, and a turn recorded under a
    blank thread id for a question nobody asked."""
    conversations = FakeConversations()
    app = assembled(conversations=conversations)

    with TestClient(api(app)) as reader:
        refused = reader.post("/api/ask", json=asked)

    assert refused.status_code == 400
    assert refused.json()["error"] == NOT_A_QUESTION
    assert conversations.sessions() == ()


def test_a_question_past_what_cora_reads_is_refused() -> None:
    """`request.json()` buffers whatever arrives, next door to the endpoint that just
    grew a ceiling. What a question may run to is the engine's rule; this is how much
    cora reads to find out."""
    body = json.dumps({"question": "x" * MAX_ASK_BYTES, "thread_id": "t1"})

    with TestClient(api(assembled())) as reader:
        refused = reader.post(
            "/api/ask", content=body, headers={"Content-Type": "application/json"}
        )

    assert refused.status_code == 413
    assert refused.json()["error"] == TOO_LONG_TO_ASK


def test_the_question_ceiling_does_not_rest_on_a_declared_length() -> None:
    """A body that declares no length is the shape a ceiling has to hold for — the
    upload route's trick, refusing on `Content-Length`, is no use to a route that must
    read a chunked body too. So the bound is on the reading."""

    def chunked() -> Iterator[bytes]:
        yield b'{"question": "'
        yield b"x" * (MAX_ASK_BYTES + 1)
        yield b'", "thread_id": "t1"}'

    with TestClient(api(assembled())) as reader:
        refused = reader.post(
            "/api/ask",
            content=chunked(),
            headers={"Content-Type": "application/json"},
        )

    assert refused.status_code == 413
    assert refused.json()["error"] == TOO_LONG_TO_ASK


def test_the_ceiling_never_refuses_a_question_the_engine_would_allow() -> None:
    """`MAX_INPUT_CHARS` is what a question may run to; the ceiling only decides how
    much is read to find that out. The other two tests build their body *from* the
    ceiling, so they hold for any value of it — including one that refuses every
    question of the length the engine allows. This one is written from the engine's
    limit instead, at the most a character can cost on the wire: `json.dumps` escapes an
    astral character as two `\\uXXXX` sequences, twelve bytes, which is what any client
    that escapes non-ASCII sends."""
    longest = json.dumps(
        {"question": "\U0001f954" * MAX_INPUT_CHARS, "thread_id": "t1"}
    )

    with TestClient(api(assembled())) as reader:
        streamed = reader.post(
            "/api/ask", content=longest, headers={"Content-Type": "application/json"}
        )

    assert streamed.status_code == 200
    assert [name for name, _ in frames(streamed.text)][-1] == "turn"


class WritesThenBreaks:
    """A model that writes half a sentence and then cannot be reached."""

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        on_text(Piece("Sleep, "))
        raise LlmError()


def test_each_piece_the_turn_writes_arrives_as_its_own_event() -> None:
    """What the reader is waiting for is the answer, and until now it arrived only with
    the turn that ended — after every step, and after the model had finished writing."""
    app = indexed(
        assembled(
            chat_model=ScriptedChatModel(
                [ModelReply(text="Sleep, not volume [1].")],
                pieces=[["Sleep, ", "not volume [1]."]],
            )
        ),
        ("notes.md", NOTES),
    )

    streamed = asking(app)

    assert [data["text"] for name, data in streamed if name == "text"] == [
        "Sleep, ",
        "not volume [1].",
    ]


def test_a_piece_arrives_before_the_step_that_ends_the_round_it_was_written_in() -> (
    None
):
    """The page resets what it is showing when a piece follows a step, so the two have
    to be ordered against each other — they are, because both reach the wire through
    the one queue this endpoint drains."""
    app = indexed(assembled(chat_model=searching()), ("notes.md", NOTES))

    names = [name for name, _ in asking(app)]

    assert names.index("text") < names.index("step", names.index("text"))
    assert names[-1] == "turn"


def test_the_turn_still_carries_the_whole_answer() -> None:
    """The page never assembles the pieces into the answer it keeps: what a reopened
    conversation redraws is what the turn event carried, so the two must agree."""
    app = indexed(
        assembled(
            chat_model=ScriptedChatModel(
                [ModelReply(text="Sleep, not volume [1].")],
                pieces=[["Sleep, ", "not volume [1]."]],
            )
        ),
        ("notes.md", NOTES),
    )

    streamed = asking(app)

    written = "".join(data["text"] for name, data in streamed if name == "text")
    assert streamed[-1][0] == "turn"
    assert streamed[-1][1]["answer"] == written


def preambling(answer: str = "Sleep, not volume [1].") -> ScriptedChatModel:
    """A model that says what it is about to do before it does it — the shape every
    claim about the wire has to survive, and the one a script with an empty first round
    quietly avoids."""
    return ScriptedChatModel(
        [
            ModelReply(text="Let me check your notes. ", tool_calls=(SEARCH,)),
            ModelReply(text=answer),
        ],
        pieces=[["Let me check ", "your notes. "], ["Sleep, ", "not volume [1]."]],
    )


def test_an_aside_marks_the_pieces_a_round_wrote_before_calling_a_tool() -> None:
    """Without it the contract is a lie a client has to know about: pieces arrive for a
    sentence that is not the answer, and only the shape of the step stream says so."""
    app = indexed(assembled(chat_model=preambling()), ("notes.md", NOTES))

    streamed = asking(app)
    names = [name for name, _ in streamed]

    written = [
        data["text"]
        for name, data in streamed[: names.index("aside")]
        if name == "text"
    ]
    assert written == ["Let me check ", "your notes. "]
    decided = next(
        at
        for at, (name, data) in enumerate(streamed)
        if name == "step" and data["summary"].startswith("Decided")
    )
    assert names.index("aside") < decided, (
        "the reader is told to drop the preamble before the round that wrote it lands"
    )


def test_a_turn_answered_in_one_round_sends_no_aside() -> None:
    """An aside has the reader drop what they have been shown, so one after a final
    would take the answer with it."""
    app = indexed(
        assembled(
            chat_model=ScriptedChatModel(
                [ModelReply(text="Sleep, not volume.")],
                pieces=[["Sleep, ", "not volume."]],
            )
        ),
        ("notes.md", NOTES),
    )

    assert [name for name, _ in asking(app)] == [
        "step",  # screen
        "step",  # route
        "step",  # the scope it settled on
        "step",  # focus
        "step",  # work
        "text",
        "text",
        "step",  # the round that answered
        "step",  # answer
        "turn",
    ]


def test_the_pieces_after_the_last_aside_are_the_answer_the_turn_carries() -> None:
    """The whole of what the wire promises, over a model that writes before it searches:
    a client keeps the pieces since the last aside and needs nothing else to know it has
    the answer."""
    app = indexed(assembled(chat_model=preambling()), ("notes.md", NOTES))

    streamed = asking(app)
    after = streamed[[name for name, _ in streamed].index("aside") + 1 :]

    written = "".join(data["text"] for name, data in after if name == "text")
    assert streamed[-1][0] == "turn"
    assert streamed[-1][1]["answer"] == written
    assert written == "Sleep, not volume [1]."


def test_a_turn_that_fails_after_writing_ends_with_the_error() -> None:
    """The pieces are not taken back on the wire — the page replaces them with the
    sentence, which is the one thing that is true about that turn."""
    app = assembled(chat_model=WritesThenBreaks())

    streamed = asking(app)

    assert [name for name, _ in streamed] == [
        "step",  # screen
        "step",  # route
        "step",  # the scope it settled on
        "step",  # focus
        "step",  # work
        "text",
        "error",
    ]
    assert streamed[-1][1]["error"] == LlmError().user_message


# ── a turn that stops to ask ──

ASKED = "Which bodyweight should I treat as current?"
STOPPING = ToolCall(
    name=ASK_TOOL_NAME,
    arguments={
        "question": ASKED,
        "options": [
            {"label": "77 kg", "note": "intake form, 17 Aug"},
            {"label": "75 kg", "note": "coach notes, February"},
        ],
        "decline": "Neither of them",
    },
    call_id="a1",
)
WEIGHED = "At 75 kg your BMR is about 1,730 kcal."


def _stopping() -> ScriptedChatModel:
    return ScriptedChatModel([ModelReply(tool_calls=(STOPPING,)), ModelReply(WEIGHED)])


def _named(streamed: str) -> list[str]:
    return [name for name, _ in frames(streamed)]


def _carried(streamed: str, event: str) -> list[dict]:
    return [data for name, data in frames(streamed) if name == event]


def test_a_turn_that_stops_to_ask_ends_its_stream_paused() -> None:
    """Not `turn`: there is no answer yet. A stream that closed with an empty turn would
    read on the page as cora having replied with nothing."""
    with TestClient(api(assembled(chat_model=_stopping()))) as reader:
        streamed = reader.post(
            "/api/ask", json={"question": "What is my BMR?", "thread_id": "t1"}
        )

    assert _named(streamed.text)[-1] == "paused"
    assert "turn" not in _named(streamed.text)


def test_the_paused_frame_carries_the_question_and_every_way_out() -> None:
    with TestClient(api(assembled(chat_model=_stopping()))) as reader:
        streamed = reader.post(
            "/api/ask", json={"question": "What is my BMR?", "thread_id": "t1"}
        )

    [paused] = _carried(streamed.text, "paused")
    assert paused == {
        "asked": "What is my BMR?",
        "card": {
            "prompt": ASKED,
            "fields": [],
            "actions": [
                {
                    "label": "77 kg",
                    "answer": "77 kg",
                    "note": "intake form, 17 Aug",
                    "needs_valid": False,
                    "settled": "",
                },
                {
                    "label": "75 kg",
                    "answer": "75 kg",
                    "note": "coach notes, February",
                    "needs_valid": False,
                    "settled": "",
                },
                {
                    "label": "Neither of them",
                    "answer": None,
                    "note": "",
                    "needs_valid": False,
                    "settled": "You chose none of them.",
                },
            ],
        },
    }


def test_picking_an_option_streams_the_rest_of_the_turn() -> None:
    app = assembled(chat_model=_stopping())
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "What is my BMR?", "thread_id": "t1"})
        resumed = reader.post(
            "/api/resume", json={"thread_id": "t1", "answer": "75 kg"}
        )

    assert resumed.status_code == 200
    assert resumed.headers["content-type"].startswith("text/event-stream")
    [turn] = _carried(resumed.text, "turn")
    assert turn["answer"] == WEIGHED


def test_choosing_nothing_still_finishes_the_turn() -> None:
    app = assembled(chat_model=_stopping())
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "What is my BMR?", "thread_id": "t1"})
        resumed = reader.post("/api/resume", json={"thread_id": "t1", "answer": None})

    [turn] = _carried(resumed.text, "turn")
    assert turn["answer"] == WEIGHED


def test_a_decision_for_a_thread_waiting_on_nothing_is_refused() -> None:
    """A card clicked twice, or one left open while the conversation moved on: a
    sentence under a status code, not a stream carrying a failure."""
    with TestClient(api(assembled(chat_model=_stopping()))) as reader:
        refused = reader.post(
            "/api/resume", json={"thread_id": "t1", "answer": "75 kg"}
        )

    assert refused.status_code == 400
    assert refused.json()["error"]


def test_a_card_answered_after_its_conversation_was_deleted_is_refused() -> None:
    """The turn was parked in a thread that no longer exists, which is the same nothing
    as a card clicked twice — and it must not run half a turn against a deleted one."""
    app = assembled(chat_model=_stopping())
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "What is my BMR?", "thread_id": "t1"})
        assert reader.delete("/api/sessions/t1").status_code == 204

        refused = reader.post(
            "/api/resume", json={"thread_id": "t1", "answer": "75 kg"}
        )

    assert refused.status_code == 400
    assert refused.json()["error"]


def test_a_decision_with_no_conversation_is_refused_like_a_question_with_none() -> None:
    with TestClient(api(assembled(chat_model=_stopping()))) as reader:
        refused = reader.post("/api/resume", json={"answer": "75 kg"})

    assert refused.status_code == 400
    assert refused.json() == {"error": NOT_A_DECISION}


def test_the_thread_reports_what_it_is_waiting_on() -> None:
    """A page that reloaded while the card was open has nowhere else to look: the turn
    is recorded only once it has an answer."""
    app = assembled(chat_model=_stopping())
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "What is my BMR?", "thread_id": "t1"})
        waiting = reader.get("/api/sessions/t1/pending")

    assert waiting.json()["card"]["prompt"] == ASKED
    assert waiting.json()["asked"] == "What is my BMR?"


def test_a_thread_waiting_on_nothing_reports_nothing() -> None:
    with TestClient(api(assembled(chat_model=_stopping()))) as reader:
        waiting = reader.get("/api/sessions/t1/pending")

    assert waiting.status_code == 200
    assert waiting.json() is None


def test_a_paused_turn_is_absent_from_the_conversation_until_it_is_answered() -> None:
    kept = FakeConversations()
    app = assembled(chat_model=_stopping(), conversations=kept)
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "What is my BMR?", "thread_id": "t1"})

        assert reader.get("/api/sessions/t1").json() == []

        reader.post("/api/resume", json={"thread_id": "t1", "answer": "75 kg"})

        [turn] = reader.get("/api/sessions/t1").json()
        assert turn["question"] == "What is my BMR?"
        assert turn["result"]["answer"] == WEIGHED


def test_a_decision_that_says_nothing_at_all_is_refused() -> None:
    """`answer` has to be said, even to say nothing. A body that leaves it out reads the
    same as one that declines, so a client with the field misspelled would quietly tell
    the model the reader rejected every option."""
    app = assembled(chat_model=_stopping())
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "What is my BMR?", "thread_id": "t1"})
        refused = reader.post("/api/resume", json={"thread_id": "t1"})

    assert refused.status_code == 400
    assert refused.json() == {"error": NOT_A_DECISION}
    assert reader.get("/api/sessions/t1/pending").json() is not None, (
        "the thread is still waiting, so the card is still answerable"
    )


# ── a turn that stopped to propose an effect ──

BOOKED = "book_it"
BOOKING = "Book the thing, which cannot be taken back"


def _effecting() -> Extension:
    def extend(cora: Host) -> None:
        cora.register_tool(
            name=BOOKED,
            description=BOOKING,
            parameter_schema={"type": "object"},
            run=lambda **_: "booked",
            effect=True,
        )

    return Extension(module="fixture_plugins.acting", extend=extend)


def _proposing() -> ScriptedChatModel:
    return ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(
                    ToolCall(name=BOOKED, arguments={"when": "May"}, call_id="c1"),
                )
            ),
            ModelReply(text="Done."),
        ]
    )


def _acting_app() -> App:
    return assembled(chat_model=_proposing(), plugin=_effecting())


def test_a_proposed_effect_is_streamed_as_the_paused_event_the_page_reads() -> None:
    """One event for both kinds of stop, carrying whichever it was: the page reads which
    card to draw off the payload rather than off a second event name."""
    with TestClient(api(_acting_app())) as reader:
        streamed = reader.post(
            "/api/ask", json={"question": "book it", "thread_id": "t1"}
        )

    [paused] = _carried(streamed.text, "paused")
    assert paused["asked"] == "book it"
    assert paused["card"]["prompt"] == BOOKING
    assert paused["card"]["fields"] == [
        {
            "name": TOOL,
            "schema": {},
            "value": BOOKED,
            "editable": False,
            "required": False,
        },
        {
            "name": "when",
            "schema": {},
            "value": "May",
            "editable": False,
            "required": False,
        },
    ]
    assert [action["answer"] for action in paused["card"]["actions"]] == ["c1", None]
    assert "turn" not in _named(streamed.text)


def test_the_pending_route_answers_with_the_proposal_a_reopened_page_must_draw() -> (
    None
):
    app = _acting_app()
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "book it", "thread_id": "t1"})

        waiting = reader.get("/api/sessions/t1/pending").json()

    assert waiting["card"]["actions"][0]["answer"] == "c1"
    assert waiting["card"]["prompt"] == BOOKING


def test_approving_a_proposal_streams_the_rest_of_the_turn() -> None:
    app = _acting_app()
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "book it", "thread_id": "t1"})
        approved = reader.post(
            "/api/resume",
            json={"thread_id": "t1", "answer": "c1"},
        )

    [turn] = _carried(approved.text, "turn")
    assert turn["answer"] == "Done."
    assert any("approved" in step["summary"] for step in turn["trace"])


def test_declining_a_proposal_still_finishes_the_turn() -> None:
    app = _acting_app()
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "book it", "thread_id": "t1"})
        declined = reader.post(
            "/api/resume",
            json={"thread_id": "t1", "answer": None},
        )

    [turn] = _carried(declined.text, "turn")
    assert turn["answer"] == "Done."
    assert any("declined" in step["summary"] for step in turn["trace"])


@pytest.mark.parametrize(
    "body",
    [
        {"answer": "c1"},
        {"thread_id": "t1"},
        {"thread_id": "t1", "answer": 7},
    ],
)
def test_an_answer_missing_half_of_what_binds_it_is_refused(body: dict) -> None:
    """An answer has to say which conversation it is in and which action was taken: a
    missing field must not read as a decline."""
    with TestClient(api(_acting_app())) as reader:
        refused = reader.post("/api/resume", json=body)

    assert refused.status_code == REFUSED
    assert refused.json() == {"error": NOT_A_DECISION}


def test_values_that_are_not_an_object_are_refused() -> None:
    with TestClient(api(_acting_app())) as reader:
        reader.post("/api/ask", json={"question": "book it", "thread_id": "t1"})
        refused = reader.post(
            "/api/resume", json={"thread_id": "t1", "answer": "c1", "values": "BER"}
        )

    assert refused.status_code == REFUSED
    assert refused.json() == {"error": NOT_FILLED_IN}


def test_a_value_for_a_field_the_card_put_up_to_be_read_never_reaches_the_run() -> None:
    """A card names which fields are the reader's. A value for anything else arrived
    from outside the run, so an argument put up for approval cannot be rewritten by the
    request that approves it."""
    app = _acting_app()
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "book it", "thread_id": "t1"})
        approved = reader.post(
            "/api/resume",
            json={"thread_id": "t1", "answer": "c1", "values": {"when": "December"}},
        )

    [turn] = _carried(approved.text, "turn")
    assert any("approved" in step["summary"] for step in turn["trace"])
    assert "December" not in approved.text


def _proposing_two() -> ScriptedChatModel:
    return ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(
                    ToolCall(name=BOOKED, arguments={"when": "May"}, call_id="c1"),
                    ToolCall(name=BOOKED, arguments={"when": "June"}, call_id="c2"),
                )
            ),
            ModelReply(text="Done."),
        ]
    )


def test_a_round_proposing_two_effects_is_answered_one_call_at_a_time() -> None:
    """The page settles each on its own, so the endpoint has to put the second proposal
    once the first is answered — and each answer names the call it belongs to."""
    app = assembled(chat_model=_proposing_two(), plugin=_effecting())
    with TestClient(api(app)) as reader:
        reader.post("/api/ask", json={"question": "book both", "thread_id": "t1"})
        first = reader.post("/api/resume", json={"thread_id": "t1", "answer": "c1"})
        second = reader.post("/api/resume", json={"thread_id": "t1", "answer": None})

    [proposed] = _carried(first.text, "paused")
    assert proposed["card"]["actions"][0]["answer"] == "c2"
    assert not _carried(first.text, "turn"), "the round is not done while one is open"
    [turn] = _carried(second.text, "turn")
    assert turn["answer"] == "Done."
    settled = [step["summary"] for step in turn["trace"] if "You " in step["summary"]]
    assert settled == [f"You approved {BOOKED}", f"You declined {BOOKED}"], (
        "one approval per call, and no duplicate from replaying the gate"
    )


def test_an_action_the_card_never_offered_is_refused_not_read_as_a_decline() -> None:
    """The step waiting would read it as a decline — safe, and silent. A page holding a
    card the conversation has moved past is told, rather than having the reader's turn
    settled the other way on its behalf."""
    with TestClient(api(assembled(chat_model=_stopping()))) as reader:
        reader.post("/api/ask", json={"question": "What is my BMR?", "thread_id": "t1"})

        refused = reader.post("/api/resume", json={"thread_id": "t1", "answer": "c1"})

    assert refused.status_code == REFUSED
    assert refused.json() == {"error": NOT_THAT_CARD}
    assert reader.get("/api/sessions/t1/pending").json() is not None, (
        "the thread is still waiting, so the card is still answerable"
    )
