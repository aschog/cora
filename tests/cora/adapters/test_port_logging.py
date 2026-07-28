from cora.adapters.port_logging import (
    MAX_LOGGED_CHARS,
    LoggingChatModel,
    truncate,
)
from cora.core.ports.chat_model import Message, ModelReply
from fakes import ScriptedChatModel, add_tool


def test_truncate_passes_text_within_the_cap_through_unchanged() -> None:
    text = "short enough to log in full"

    assert truncate(text) == text


def test_truncate_bounds_long_text_and_marks_the_cut() -> None:
    clipped = truncate("x" * (MAX_LOGGED_CHARS * 3))

    assert len(clipped) <= MAX_LOGGED_CHARS
    assert clipped.endswith("…")


def test_logging_chat_model_delegates_and_returns_the_inner_reply() -> None:
    inner = ScriptedChatModel([ModelReply(text="an answer")])
    messages = (Message(role="user", content="a question"),)
    tools = (add_tool(),)

    reply = LoggingChatModel(inner).complete(messages, tools)

    assert reply == ModelReply(text="an answer")
    assert inner.last_messages == messages
    assert inner.last_tools == tools
