import threading

from app_builder import assembled
from cora.frontends.react.api import api
from cora.ports.chat_model import Message, ModelReply, Piece, TextSink, Tool, unheard
from fakes import FakeConversations, ScriptedChatModel
from fixture_plugins import make_plugin
from sse import frames
from streaming import driven, turn_thread

TURN_ENDS = 5.0
ASKED = {"question": "Why?", "thread_id": "t1"}


# Writes half an answer, waits to be let go, and says whether it ever finished.
class WritesInTwo:
    def __init__(self, released: threading.Event) -> None:
        self._released = released
        self.finished = threading.Event()

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        on_text(Piece("Half "))
        assert self._released.wait(TURN_ENDS)
        on_text(Piece("an answer."))
        self.finished.set()
        return ModelReply(text="Half an answer.")


class StoppedThenAnswers:
    def __init__(self, released: threading.Event) -> None:
        self._released = released
        self.calls = 0
        self.last_messages: tuple[Message, ...] = ()

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        self.calls += 1
        self.last_messages = messages
        if self.calls == 1:
            on_text(Piece("Half "))
            assert self._released.wait(TURN_ENDS)
            on_text(Piece("too late."))
            return ModelReply(text="Half too late.")
        on_text(Piece("Second."))
        return ModelReply(text="Second.")


def test_a_turn_stopped_mid_prose_ends_at_the_next_piece() -> None:
    released = threading.Event()
    model = WritesInTwo(released)
    app = assembled(chat_model=model, plugin=make_plugin(), searching=False)

    read = driven(api(app), "/api/ask", ASKED, until=_wrote_something)

    turn = turn_thread()
    released.set()
    turn.join(TURN_ENDS)
    assert not turn.is_alive()
    assert not model.finished.is_set()
    assert [data["text"] for name, data in read if name == "text"] == ["Half "]


def test_a_stopped_turn_is_recorded_in_no_conversation() -> None:
    released = threading.Event()
    conversations = FakeConversations()
    app = assembled(
        chat_model=WritesInTwo(released),
        plugin=make_plugin(),
        searching=False,
        conversations=conversations,
    )

    driven(api(app), "/api/ask", ASKED, until=_wrote_something)

    turn = turn_thread()
    released.set()
    turn.join(TURN_ENDS)
    assert conversations.turns("t1") == ()
    assert conversations.opened() == ()


def test_a_stopped_turn_is_not_read_back_by_the_next_question() -> None:
    released = threading.Event()
    model = StoppedThenAnswers(released)
    app = assembled(chat_model=model, plugin=make_plugin(), searching=False)
    served = api(app)

    driven(served, "/api/ask", ASKED, until=_wrote_something)

    turn = turn_thread()
    released.set()
    turn.join(TURN_ENDS)
    read = driven(
        served,
        "/api/ask",
        {"question": "Second?", "thread_id": "t1"},
        until=lambda _: False,
    )

    assert [data["answer"] for name, data in read if name == "turn"] == ["Second."]
    assert [
        message.content for message in model.last_messages if message.role == "user"
    ] == ["Second?"]


def test_a_turn_nobody_stopped_is_recorded_and_answered() -> None:
    conversations = FakeConversations()
    app = assembled(
        chat_model=ScriptedChatModel([ModelReply(text="Sleep, not volume.")]),
        plugin=make_plugin(),
        searching=False,
        conversations=conversations,
    )

    read = driven(api(app), "/api/ask", ASKED, until=lambda _: False)

    assert [data["answer"] for name, data in read if name == "turn"] == [
        "Sleep, not volume."
    ]
    assert [turn.question for turn in conversations.turns("t1")] == ["Why?"]


def _wrote_something(read: str) -> bool:
    return any(name == "text" for name, _ in frames(read))
