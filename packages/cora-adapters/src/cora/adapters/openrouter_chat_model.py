from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI

from cora.core.errors import LlmError
from cora.core.ports.chat_model import Message, ModelReply
from cora.core.ports.plugin import Tool, ToolCall

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def to_model_reply(reply: AIMessage) -> ModelReply:
    tool_calls = tuple(
        ToolCall(name=call["name"], arguments=call["args"], call_id=call["id"] or "")
        for call in reply.tool_calls
    )
    return ModelReply(text=str(reply.text), tool_calls=tool_calls)


def to_tool_schema(tool: Tool) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameter_schema,
        },
    }


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


class OpenRouterChatModel:
    def __init__(
        self, model: str, api_key: str, base_url: str = OPENROUTER_BASE_URL
    ) -> None:
        self._client = ChatOpenAI(model=model, api_key=api_key, base_url=base_url)

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        client = self._client
        if tools:
            client = self._client.bind_tools([to_tool_schema(tool) for tool in tools])
        lc_messages = [to_langchain_message(message) for message in messages]
        try:
            reply = client.invoke(lc_messages)
        except Exception as exc:
            raise LlmError from exc
        return to_model_reply(reply)
