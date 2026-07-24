from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from core.chat_model import Message, ModelReply
from core.plugin import ToolCall


def to_model_reply(reply: AIMessage) -> ModelReply:
    tool_calls = tuple(
        ToolCall(name=call["name"], arguments=call["args"], call_id=call["id"] or "")
        for call in reply.tool_calls
    )
    return ModelReply(text=str(reply.text), tool_calls=tool_calls)


def to_langchain_message(message: Message) -> BaseMessage:
    if message.role == "system":
        return SystemMessage(content=message.content)
    if message.role == "user":
        return HumanMessage(content=message.content)
    if message.role == "assistant":
        return AIMessage(
            content=message.content,
            tool_calls=[
                {
                    "name": call.name,
                    "args": call.arguments,
                    "id": call.call_id,
                    "type": "tool_call",
                }
                for call in message.tool_calls
            ],
        )
    assert message.tool_call_id is not None
    return ToolMessage(content=message.content, tool_call_id=message.tool_call_id)
