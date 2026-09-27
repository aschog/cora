import threading

from app_builder import assembled
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import Tool, ToolCall
from fakes import ScriptedChatModel
from fixture_plugins import make_plugin
from sse import frames
from streaming import driven, turn_thread

WAITING = ToolCall(name="waiting", arguments={"x": 1}, call_id="c1")
TURN_ENDS = 5.0


def waiting_on(released: threading.Event) -> Tool:
    def run(x: int) -> int:
        assert released.wait(TURN_ENDS)
        return x

    return Tool(
        name="waiting",
        description="Waits until the test lets it go.",
        parameter_schema={
            "type": "object",
            "properties": {"x": {"type": "integer"}},
            "required": ["x"],
        },
        run=run,
    )


def test_a_reader_who_stops_leaves_the_model_unasked_for_the_next_round() -> None:
    released = threading.Event()
    model = ScriptedChatModel(
        [ModelReply(tool_calls=(WAITING,)), ModelReply(text="Too late.")]
    )
    app = assembled(
        chat_model=model,
        plugin=make_plugin(tools=(waiting_on(released),)),
        searching=False,
    )

    read = driven(
        api(app),
        "/api/ask",
        {"question": "Why?", "thread_id": "t1"},
        until=_round_decided,
    )

    # Held while it is still in the tool, and let go of only now: the reader is gone, so
    # what the turn does next is what this is about.
    turn = turn_thread()
    released.set()
    turn.join(TURN_ENDS)
    assert not turn.is_alive()
    assert model.completions == 1
    assert [name for name, _ in read] == ["step"] * len(read)


def _round_decided(read: str) -> bool:
    return any(
        name == "step" and data["summary"].startswith("Decided to call")
        for name, data in frames(read)
    )
