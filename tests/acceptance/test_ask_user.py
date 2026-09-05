"""The outer test for story 24."""

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
