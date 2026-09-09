"""The outer test for the one-value rule."""

from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import App
from cora.domain.card import ActionOffered, Card, FieldAsked
from cora.engine.ask_tool import ASK_FOR_TOOL_NAME
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.host import Extension, Host
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel
from sse import frames

HEIGHT = "Your height in metres"
NEEDS_ONE = "To work out your BMI I need your height."
ASKED_IN_PROSE = "I have your weight, but not your height in metres — what is it?"
BMI_THREAD = "the-bmi-i-asked-for"
TRIP_THREAD = "the-trip-i-confirm"

CONFIRM_TOOL = "price_the_trip"
WORKED_OUT = "Three days in Kyoto from 7 September. Shall I price that?"
TRIP = "Kyoto, 7 to 10 September"
PRICED = "Three days in Kyoto comes to 840 euro."
CONFIRMED = "You confirmed the trip."

# One field, and nobody writes in it: the reader is confirming what cora worked out
# rather than being asked for anything, so this card is not an ask.
CONFIRM = Card(
    prompt=WORKED_OUT,
    fields=(FieldAsked(name="trip", value=TRIP, editable=False),),
    actions=(
        ActionOffered(label="Price it", answer="Price it", settled=CONFIRMED),
        ActionOffered(label="Not now", answer=None),
    ),
)


def _confirming(cora: Host) -> None:
    cora.register_tool(
        name=CONFIRM_TOOL,
        description="Price the trip, once the reader has confirmed it.",
        parameter_schema={"type": "object", "properties": {"trip": {"type": "string"}}},
        run=lambda **_: PRICED,
        asks=lambda _: CONFIRM,
    )


def _app(*replies: ModelReply) -> App:
    return assembled(
        chat_model=ScriptedChatModel(list(replies)),
        plugins=(Extension(module="confirming", extend=_confirming),),
    )


def _asking_for_one() -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(
                name=ASK_FOR_TOOL_NAME,
                arguments={
                    "prompt": NEEDS_ONE,
                    "fields": [{"name": "height", "description": HEIGHT}],
                },
                call_id="a1",
            ),
        )
    )


def _pricing() -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(name=CONFIRM_TOOL, arguments={"trip": TRIP}, call_id="c1"),
        )
    )


def _of(body: str, name: str) -> list[dict]:
    return [data for event, data in frames(body) if event == name]


def test_one_value_is_asked_for_in_prose_and_a_confirm_card_still_stands() -> None:
    """The criterion, both ways round: a single value cora is missing is asked for in
    the answer and stops nothing, while a card of one field nobody writes in is not an
    ask and stops the turn as it always did."""
    with TestClient(api(_app(_asking_for_one(), ModelReply(text=ASKED_IN_PROSE)))) as (
        reader
    ):
        asked = reader.post(
            "/api/ask", json={"question": "What is my BMI?", "thread_id": BMI_THREAD}
        )

    assert _of(asked.text, "paused") == [], "one value stops nothing"
    [turn] = _of(asked.text, "turn")
    assert turn["answer"] == ASKED_IN_PROSE, "the answer is where it asks"

    with TestClient(api(_app(_pricing(), ModelReply(text=PRICED)))) as reader:
        proposed = reader.post(
            "/api/ask",
            json={"question": "Price the days in Kyoto.", "thread_id": TRIP_THREAD},
        )
        [waiting] = _of(proposed.text, "paused")
        confirmed = reader.post(
            "/api/resume", json={"thread_id": TRIP_THREAD, "answer": "Price it"}
        )

    assert waiting["card"]["prompt"] == WORKED_OUT
    assert [field["editable"] for field in waiting["card"]["fields"]] == [False]
    [turn] = _of(confirmed.text, "turn")
    assert turn["answer"] == PRICED
