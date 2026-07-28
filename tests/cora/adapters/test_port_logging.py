import logging

import pytest

from cora.adapters.port_logging import (
    MAX_LOGGED_CHARS,
    LoggingChatModel,
    truncate,
)
from cora.core.ports.chat_model import Message, ModelReply
from cora.core.ports.plugin import ToolCall
from fakes import ScriptedChatModel, add_tool


def line_about(caplog: pytest.LogCaptureFixture, subject: str) -> str:
    matches = [r.getMessage() for r in caplog.records if subject in r.getMessage()]
    assert len(matches) == 1, f"expected one line about {subject!r}, got {matches}"
    return matches[0]


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


def test_logging_chat_model_logs_the_request(caplog: pytest.LogCaptureFixture) -> None:
    inner = ScriptedChatModel([ModelReply(text="an answer")])
    messages = (
        Message(role="system", content="be helpful"),
        Message(role="user", content="a question"),
    )

    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingChatModel(inner).complete(messages, ())

    request = line_about(caplog, "request")
    assert "2 messages" in request
    assert "system, user" in request
    assert "a question" in request
    assert all(record.name.startswith("cora") for record in caplog.records)


def test_logging_chat_model_logs_the_reply(caplog: pytest.LogCaptureFixture) -> None:
    inner = ScriptedChatModel(
        [
            ModelReply(
                text="here it comes: " + "filler " * MAX_LOGGED_CHARS + "TAIL",
                tool_calls=(ToolCall(name="add", arguments={"a": 1}, call_id="c1"),),
            )
        ]
    )

    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingChatModel(inner).complete((Message(role="user", content="hi"),), ())

    reply = line_about(caplog, "reply")
    assert "add" in reply
    assert "here it comes" in reply
    assert "TAIL" not in reply


def test_logging_chat_model_never_logs_a_buried_marker(
    caplog: pytest.LogCaptureFixture,
) -> None:
    buried = "filler " * MAX_LOGGED_CHARS + "BURIED"
    inner = ScriptedChatModel([ModelReply(text=buried)])
    messages = (
        Message(role="system", content=buried),
        Message(role="user", content=buried),
    )

    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingChatModel(inner).complete(messages, ())

    logged = [record.getMessage() for record in caplog.records]
    assert len(logged) == 2
    assert not any("BURIED" in line for line in logged)


def test_logging_chat_model_bounds_the_roles_of_a_long_history(
    caplog: pytest.LogCaptureFixture,
) -> None:
    history = tuple(
        Message(role="user" if turn % 2 == 0 else "assistant", content="short")
        for turn in range(200)
    )
    inner = ScriptedChatModel([ModelReply(text="ok")])

    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingChatModel(inner).complete(history, ())

    request = line_about(caplog, "request")
    assert "200 messages" in request
    assert len(request) <= 3 * MAX_LOGGED_CHARS
