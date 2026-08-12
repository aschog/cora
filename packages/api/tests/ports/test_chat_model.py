from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall


def test_reply_is_final_without_tool_calls() -> None:
    assert ModelReply().is_final is True


def test_reply_is_not_final_with_tool_calls() -> None:
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="call-1")

    assert ModelReply(tool_calls=(call,)).is_final is False
