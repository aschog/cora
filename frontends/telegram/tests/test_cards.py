from cora.domain.approval import APPROVE, DECLINE, TOOL
from cora.domain.card import ActionOffered, Card, FieldAsked
from cora.domain.decision import NO_OPTION
from cora.engine.ask_tool import ASK_FOR_TOOL_NAME, ASK_TOOL_NAME, NOT_NOW, SEND
from cora.frontends.telegram.bot import Message, answering, taken
from cora.ports.chat_model import ModelReply
from cora.ports.host import Extension, Host
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel
from telegram_fakes import ALLOWED, FakeTelegram, chatting

QUESTION = "Which bodyweight is current?"
FIRST = "75 kg"
SECOND = "78 kg"
NOTE = "coach notes, February"
SETTLED = "75 kg it is."

ASKING = ModelReply(
    tool_calls=(
        ToolCall(
            name=ASK_TOOL_NAME,
            arguments={
                "question": QUESTION,
                "options": [
                    {"label": FIRST, "note": NOTE},
                    {"label": SECOND, "note": "your message in March"},
                ],
            },
            call_id="a1",
        ),
    )
)
ASKING_FOR = ModelReply(
    tool_calls=(
        ToolCall(
            name=ASK_FOR_TOOL_NAME,
            arguments={
                "prompt": "What should the trip be?",
                "fields": [
                    {"name": "where", "description": "Where to.", "required": True},
                    {"name": "when", "description": "What month.", "required": True},
                ],
            },
            call_id="f1",
        ),
    )
)


def _deciding() -> ScriptedChatModel:
    return ScriptedChatModel([ASKING, ModelReply(text=SETTLED)])


def test_a_paused_turn_puts_the_card_with_its_ways_off_numbered() -> None:
    telegram = FakeTelegram(Message(ALLOWED, "How heavy am I?"))

    answering(chatting(chat_model=_deciding()), telegram, allowed=(ALLOWED,))

    [sent] = telegram.texts
    assert QUESTION in sent
    assert f"1. {FIRST}" in sent
    assert NOTE in sent
    assert f"2. {SECOND}" in sent
    assert f"3. {NO_OPTION}" in sent


def test_a_number_finishes_the_turn_on_that_way_off() -> None:
    telegram = FakeTelegram(Message(ALLOWED, "How heavy am I?"), Message(ALLOWED, "1"))

    answering(chatting(chat_model=_deciding()), telegram, allowed=(ALLOWED,))

    assert telegram.texts[-1] == SETTLED


def test_a_reply_naming_no_way_off_leaves_the_turn_parked() -> None:
    app = chatting(chat_model=_deciding())
    telegram = FakeTelegram(
        Message(ALLOWED, "How heavy am I?"), Message(ALLOWED, "the heavier one")
    )

    answering(app, telegram, allowed=(ALLOWED,))

    assert "1" in telegram.texts[-1] and "3" in telegram.texts[-1]
    assert app.agent.pending(str(ALLOWED)) is not None


def test_a_way_off_waiting_on_a_value_the_chat_cannot_write_is_not_offered() -> None:
    telegram = FakeTelegram(Message(ALLOWED, "Plan me a trip"))

    answering(
        chatting(chat_model=ScriptedChatModel([ASKING_FOR, ModelReply(text="ok")])),
        telegram,
        allowed=(ALLOWED,),
    )

    [sent] = telegram.texts
    assert SEND not in sent
    assert f"1. {NOT_NOW}" in sent


def test_the_values_a_card_carries_travel_back_as_they_came() -> None:
    card = Card(
        prompt="Save this trip?",
        fields=(
            FieldAsked(name="title", value="kyoto-three-days", editable=True),
            FieldAsked(name=TOOL, value="save_itinerary", editable=False),
        ),
        actions=(
            ActionOffered(label=APPROVE, answer="s1"),
            ActionOffered(label=DECLINE, answer=None),
        ),
    )

    settled = taken(card, "1")

    assert settled is not None
    assert settled.action == "s1"
    assert settled.values == {"title": "kyoto-three-days"}


def test_a_reply_that_names_nothing_settles_nothing() -> None:
    card = Card(
        prompt="Save this trip?",
        actions=(
            ActionOffered(label=APPROVE, answer="s1"),
            ActionOffered(label=DECLINE, answer=None),
        ),
    )

    assert taken(card, "3") is None
    assert taken(card, "0") is None
    assert taken(card, "yes") is None
    assert taken(card, "") is None
    # A digit `int` refuses to read: taken for a choice, it would raise mid-turn.
    assert taken(card, "\u00b2") is None


def test_a_bot_started_while_a_chat_is_parked_reads_the_card_off_the_agent() -> None:
    app = chatting(chat_model=_deciding())
    answering(
        app, FakeTelegram(Message(ALLOWED, "How heavy am I?")), allowed=(ALLOWED,)
    )

    second = FakeTelegram(Message(ALLOWED, "1"))
    answering(app, second, allowed=(ALLOWED,))

    assert second.texts == [SETTLED]


def test_an_effect_is_approved_from_the_chat() -> None:
    """The card a plugin really puts up: an effect, its arguments laid out, and a yes
    that is the one thing between the model's call and the world."""
    ran: list[int] = []

    def notify(x: int) -> int:
        ran.append(x)
        return x

    def extend(cora: Host) -> None:
        cora.register_tool(
            name="notify",
            description="Notify someone.",
            parameter_schema={
                "type": "object",
                "properties": {"x": {"type": "integer"}},
                "required": ["x"],
            },
            run=notify,
            effect=True,
        )

    model = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(ToolCall(name="notify", arguments={"x": 7}, call_id="e1"),)
            ),
            ModelReply(text="Done."),
        ]
    )
    telegram = FakeTelegram(Message(ALLOWED, "notify me"), Message(ALLOWED, "1"))

    answering(
        chatting(
            chat_model=model,
            plugin=Extension(module="fixture_plugins.effecting", extend=extend),
        ),
        telegram,
        allowed=(ALLOWED,),
    )

    card = telegram.texts[0]
    assert card.index("x: 7") < card.index("1."), card
    assert ran == [7]
    assert telegram.texts[-1] == "Done."
