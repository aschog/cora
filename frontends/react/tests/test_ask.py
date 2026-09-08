import json
import logging

import pytest
from starlette.testclient import TestClient

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.domain.approval import TOOL
from cora.domain.errors import LlmError
from cora.engine.ask_tool import ASK_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.react.api import (
    MAX_ASK_BYTES,
    NOT_A_DECISION,
    NOT_FILLED_IN,
    NOT_THAT_CARD,
    REFUSED,
    TOO_LONG_TO_ASK,
    api,
)
from cora.ports.chat_model import Message, ModelReply, TextSink, unheard
from cora.ports.host import Extension, Host
from cora.ports.plugin import Tool, ToolCall
from fakes import ScriptedChatModel
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


"""How long the run is given. Long enough that a slow machine still streams, and well
inside the model's own patience below — a turn that batches its events must fail on
*this* deadline, not be rescued by the model giving up and finishing anyway."""

"""The model waits to be released rather than to be timed out; the number is only a
backstop so a test that never releases cannot hang the suite."""


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


@pytest.mark.parametrize(
    "body",
    [
        {"answer": "c1"},
        {"thread_id": "t1"},
        {"thread_id": "t1", "answer": 7},
        {"thread_id": "t1", "answer": "c1", "values": "BER"},
    ],
)
def test_an_answer_that_does_not_bind_to_a_card_is_refused(body: dict) -> None:
    """An answer has to say which conversation it is in and which action was taken, and
    what it fills in has to be fields: a missing half must not read as a decline, and a
    `values` that is not an object must not reach the run.

    This is the route an effect is approved on, so what it accepts is the width of what
    can authorise one.
    """
    with TestClient(api(_acting_app())) as reader:
        reader.post("/api/ask", json={"question": "book it", "thread_id": "t1"})
        refused = reader.post("/api/resume", json=body)

    assert refused.status_code == REFUSED
    assert refused.json()["error"] in (NOT_A_DECISION, NOT_FILLED_IN)
