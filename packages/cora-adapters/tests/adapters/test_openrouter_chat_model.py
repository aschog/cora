import pytest
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from cora.adapters.openrouter_chat_model import (
    OpenRouterChatModel,
    to_langchain_message,
    to_model_reply,
)
from cora.core.errors import LlmError
from cora.core.ports.chat_model import Message, ModelReply
from cora.core.ports.plugin import ToolCall
from fakes import add_tool


class _FakeChatOpenAI:
    last: "_FakeChatOpenAI | None" = None

    def __init__(self, **kwargs: object) -> None:
        _FakeChatOpenAI.last = self
        self.init_kwargs = kwargs
        self.bound_tools: list[dict[str, object]] | None = None

    def bind_tools(self, tools: list[dict[str, object]]) -> "_FakeChatOpenAI":
        self.bound_tools = tools
        return self

    def invoke(self, messages: object) -> AIMessage:
        return AIMessage(content="ok")


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


def test_tool_schemas_are_bound_onto_the_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cora.adapters.openrouter_chat_model.ChatOpenAI", _FakeChatOpenAI
    )
    tool = add_tool()
    model = OpenRouterChatModel(model="m", api_key="k")

    model.complete((Message(role="user", content="hi"),), (tool,))

    assert _FakeChatOpenAI.last is not None
    assert _FakeChatOpenAI.last.bound_tools == [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameter_schema,
            },
        }
    ]


def test_provider_exception_is_wrapped_as_llm_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FailingChatOpenAI:
        def __init__(self, **kwargs: object) -> None: ...

        def invoke(self, messages: object) -> AIMessage:
            raise RuntimeError("provider down")

    monkeypatch.setattr(
        "cora.adapters.openrouter_chat_model.ChatOpenAI", _FailingChatOpenAI
    )
    model = OpenRouterChatModel(model="m", api_key="k")

    with pytest.raises(LlmError):
        model.complete((Message(role="user", content="hi"),), ())


def test_complete_returns_the_mapped_model_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cora.adapters.openrouter_chat_model.ChatOpenAI", _FakeChatOpenAI
    )
    model = OpenRouterChatModel(model="m", api_key="k")

    reply = model.complete((Message(role="user", content="hi"),), ())

    assert reply == ModelReply(text="ok")
