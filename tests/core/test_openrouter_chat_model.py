from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from core.chat_model import Message, ModelReply
from core.openrouter_chat_model import to_langchain_message, to_model_reply
from core.plugin import ToolCall


def test_system_message_maps_to_langchain_system_message() -> None:
    result = to_langchain_message(Message(role="system", content="sys"))

    assert isinstance(result, SystemMessage)
    assert result.content == "sys"


def test_user_message_maps_to_human_message() -> None:
    result = to_langchain_message(Message(role="user", content="hi"))

    assert isinstance(result, HumanMessage)
    assert result.content == "hi"


def test_assistant_with_tool_calls_maps_to_ai_message() -> None:
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")

    result = to_langchain_message(
        Message(role="assistant", content="", tool_calls=(call,))
    )

    assert isinstance(result, AIMessage)
    assert result.tool_calls == [
        {"name": "add", "args": {"a": 1, "b": 2}, "id": "c1", "type": "tool_call"}
    ]


def test_tool_message_maps_to_langchain_tool_message() -> None:
    result = to_langchain_message(Message(role="tool", content="3", tool_call_id="c1"))

    assert isinstance(result, ToolMessage)
    assert result.content == "3"
    assert result.tool_call_id == "c1"


def test_provider_reply_with_tool_calls_becomes_model_reply_tool_calls() -> None:
    ai = AIMessage(
        content="",
        tool_calls=[
            {"name": "add", "args": {"a": 1, "b": 2}, "id": "c1", "type": "tool_call"}
        ],
    )

    reply = to_model_reply(ai)

    assert reply == ModelReply(
        text="",
        tool_calls=(ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1"),),
    )
    assert reply.is_final is False


def test_provider_text_reply_becomes_final_model_reply() -> None:
    reply = to_model_reply(AIMessage(content="The sum is 3."))

    assert reply == ModelReply(text="The sum is 3.", tool_calls=())
    assert reply.is_final is True
