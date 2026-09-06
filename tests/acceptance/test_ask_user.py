"""The outer tests for story 24, and for cora asking for what it does not hold."""

from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import App
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeMemory, ScriptedChatModel
from sse import frames

THREAD = "the-conversation-that-stops"
QUESTION = "What is my BMR?"
KEPT = (
    "bodyweight 77 kg, from the intake form on 17 Aug",
    "bodyweight 75 kg, from the coach notes in February",
    "bodyweight 85 kg, from the physio letter",
)
ASKED = "Which bodyweight should I treat as current?"
OFFERED = [
    {"label": "77 kg", "note": "most recent — logged 17 Aug, intake form"},
    {"label": "75 kg", "note": "coach notes, February"},
    {"label": "85 kg", "note": "physio letter — likely a typo"},
]
DECLINE = "Don't use any of them — I'll tell you later"
CHOSEN = "75 kg"
ANSWER = "At 75 kg your BMR is about 1,730 kcal."


def _asking() -> ModelReply:
    from cora.engine.ask_tool import ASK_TOOL_NAME

    return ModelReply(
        tool_calls=(
            ToolCall(
                name=ASK_TOOL_NAME,
                arguments={"question": ASKED, "options": OFFERED, "decline": DECLINE},
                call_id="a1",
            ),
        )
    )


def _app(model: ScriptedChatModel) -> App:
    return assembled(chat_model=model, memory=FakeMemory(KEPT))


def _of(body: str, name: str) -> list[dict]:
    return [data for event, data in frames(body) if event == name]


def test_a_fact_recalled_three_ways_stops_the_turn_and_the_pick_answers_it() -> None:
    """The criterion: memory holds one fact at three values, cora stops rather than
    guessing, and the value chosen is the one the answer rests on."""
    model = ScriptedChatModel([_asking(), ModelReply(text=ANSWER)])
    with TestClient(api(_app(model))) as reader:
        asked = reader.post(
            "/api/ask", json={"question": QUESTION, "thread_id": THREAD}
        )
        resumed = reader.post(
            "/api/resume", json={"thread_id": THREAD, "answer": CHOSEN}
        )

    [paused] = _of(asked.text, "paused")
    assert paused["asked"] == QUESTION
    assert paused["card"]["prompt"] == ASKED
    assert paused["card"]["fields"] == [], "there is nothing to fill in, only to pick"
    assert [action["label"] for action in paused["card"]["actions"]] == [
        "77 kg",
        "75 kg",
        "85 kg",
        DECLINE,
    ]
    assert not _of(asked.text, "turn"), "a paused turn is not an answered one"

    [turn] = _of(resumed.text, "turn")
    assert turn["answer"] == ANSWER
    said = model.last_messages or ()
    assert any(message.content == CHOSEN for message in said), (
        "the pick is what the model was told, so the answer rests on it"
    )


TRIP = "I want to go to Madrid"
WANTED = "Give me the trip and I'll price it."
FIELDS = [
    {"name": "origin", "description": "Where you are flying from", "required": True},
    {
        "name": "depart",
        "description": "The day you leave",
        "format": "date",
        "required": True,
    },
    {
        "name": "nights",
        "description": "How many nights away",
        "type": "integer",
        "required": True,
    },
    {
        "name": "budget",
        "description": "What you want to spend",
        "choices": ["Lean", "Middle", "No cap"],
    },
]
WRITTEN = {
    "origin": "BER",
    "depart": "2026-10-01",
    "nights": 4,
    "budget": "Middle",
}
PLANNED = "Four nights in Madrid from BER on 1 October, on a middling budget."


def _asking_for() -> ModelReply:
    from cora.engine.ask_tool import ASK_FOR_TOOL_NAME

    return ModelReply(
        tool_calls=(
            ToolCall(
                name=ASK_FOR_TOOL_NAME,
                arguments={"prompt": WANTED, "fields": FIELDS},
                call_id="f1",
            ),
        )
    )


def test_four_values_cora_does_not_hold_are_asked_as_one_card() -> None:
    """The criterion: an answer needing four values nobody holds stops on one card of
    them, and rests on what the reader wrote rather than on a list of questions."""
    from cora.engine.ask_tool import SEND

    model = ScriptedChatModel([_asking_for(), ModelReply(text=PLANNED)])
    with TestClient(api(_app(model))) as reader:
        asked = reader.post("/api/ask", json={"question": TRIP, "thread_id": THREAD})
        resumed = reader.post(
            "/api/resume",
            json={"thread_id": THREAD, "answer": SEND, "values": WRITTEN},
        )

    [paused] = _of(asked.text, "paused")
    assert paused["asked"] == TRIP
    assert paused["card"]["prompt"] == WANTED
    drawn = paused["card"]["fields"]
    assert [field["name"] for field in drawn] == [
        "origin",
        "depart",
        "nights",
        "budget",
    ]
    assert [field["required"] for field in drawn] == [True, True, True, False]
    assert drawn[1]["schema"]["format"] == "date", "a day is asked for as a day"
    assert drawn[2]["schema"]["type"] == "integer"
    assert drawn[3]["schema"]["enum"] == ["Lean", "Middle", "No cap"]
    assert not _of(asked.text, "turn"), "a paused turn is not an answered one"

    [turn] = _of(resumed.text, "turn")
    assert turn["answer"] == PLANNED
    said = model.last_messages or ()
    filled = [message for message in said if message.tool_call_id == "f1"]
    assert filled and all(
        str(value) in filled[0].content for value in WRITTEN.values()
    ), "what the reader wrote is what the model was told"
