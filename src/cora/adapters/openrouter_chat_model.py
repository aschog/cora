from typing import Any

import openai
from langchain_core.exceptions import ContextOverflowError
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI

from cora.domain.errors import (
    LlmBusyError,
    LlmConversationTooLongError,
    LlmEmptyReplyError,
    LlmError,
    LlmKeyRejectedError,
    LlmTimeoutError,
    LlmTruncatedError,
)
from cora.ports.chat_model import Message, ModelReply, TextSink, unheard
from cora.ports.plugin import Tool, ToolCall

MAX_RETRIES = 2

_CATEGORIES: tuple[tuple[type[Exception], type[LlmError]], ...] = (
    (ContextOverflowError, LlmConversationTooLongError),
    (openai.APITimeoutError, LlmTimeoutError),
    (openai.RateLimitError, LlmBusyError),
    (openai.AuthenticationError, LlmKeyRejectedError),
)
"""Ordered, not a mapping: the provider's classes overlap by inheritance, and the
overflow errors are `BadRequestError`/`APIError` subclasses that a broader entry would
swallow. First match wins, so the most specific category comes first."""


def to_model_reply(reply: AIMessage) -> ModelReply:
    """Raises rather than returns when the provider stopped early: a final with no
    usable text is a failed turn, and returning it hands the user a blank or half a
    sentence as though it were the answer."""
    tool_calls = tuple(
        ToolCall(name=call["name"], arguments=call["args"], call_id=call["id"] or "")
        for call in reply.tool_calls
    )
    text = str(reply.text)
    if not tool_calls:
        if reply.response_metadata.get("finish_reason") == "length":
            raise LlmTruncatedError
        if not text.strip():
            raise LlmEmptyReplyError
    return ModelReply(text=text, tool_calls=tool_calls)


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
        self,
        model: str,
        api_key: str,
        base_url: str,
        max_output_tokens: int,
        request_timeout_seconds: int,
        reasoning_effort: str,
    ) -> None:
        """The endpoint and the budgets are passed in, never assumed: which host
        answers, how long an answer may run and how much of it the model may spend
        thinking are the deployment's choice, made alongside the model they belong to,
        and `cora.app.config` is where they are written down."""
        self._client = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=request_timeout_seconds,
            max_retries=MAX_RETRIES,
            max_tokens=max_output_tokens,
            extra_body={"reasoning": {"effort": reasoning_effort}},
        )

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        """The reply is streamed and returned whole. A turn is built from the whole —
        the transcript it appends to, the answer it records, the tool call it routes on
        — and `on_text` is that same text reaching the reader while it is still being
        written."""
        client = self._client
        if tools:
            client = self._client.bind_tools([to_tool_schema(tool) for tool in tools])
        lc_messages = [to_langchain_message(message) for message in messages]
        return to_model_reply(_streamed(client, lc_messages, on_text))


def _streamed(client: Any, messages: list[BaseMessage], on_text: TextSink) -> AIMessage:
    """The pieces, handed on as they land and added up as they go. Text is what a reader
    is shown, so a piece carrying only reasoning or a fragment of a tool call is added
    to the whole and passed on to nobody.

    A stream that fails part-way fails as its category, like a whole reply that never
    arrived. The pieces already handed on are not taken back: the caller replaces them
    with the sentence the failure carries."""
    whole: AIMessageChunk | None = None
    try:
        for piece in client.stream(messages):
            whole = piece if whole is None else whole + piece
            if piece.text:
                on_text(piece.text)
    except Exception as exc:
        raise _categorise(exc) from exc
    if whole is None:
        raise LlmEmptyReplyError
    return whole


def _categorise(exc: Exception) -> LlmError:
    for provider_error, wrapped in _CATEGORIES:
        if isinstance(exc, provider_error):
            return wrapped()
    return LlmError()
