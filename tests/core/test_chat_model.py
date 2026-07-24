import dataclasses

import pytest

from core.ports.chat_model import Message, ModelReply
from core.ports.plugin import ToolCall


def test_reply_is_final_without_tool_calls() -> None:
    assert ModelReply().is_final is True


def test_reply_is_not_final_with_tool_calls() -> None:
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="call-1")

    assert ModelReply(tool_calls=(call,)).is_final is False


def test_message_is_immutable() -> None:
    message = Message(role="user", content="hi")

    with pytest.raises(dataclasses.FrozenInstanceError):
        message.content = "changed"  # ty: ignore[invalid-assignment]
